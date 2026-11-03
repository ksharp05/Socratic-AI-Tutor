from pathlib import Path
from datetime import datetime,timezone
import concurrent.futures,hashlib,json,subprocess,zipfile,re,urllib.parse,threading
ROOT=Path.cwd();BASE=ROOT/'Directions/ncert_all_subjects_8_12/2026-11-03';selection=json.loads((BASE/'selection.json').read_text(encoding='utf-8'))
MATH=ROOT/'Directions/ncert_maths_8_12/2026-11-03';math=json.loads((MATH/'MANIFEST.json').read_text(encoding='utf-8'));maths={b['book_code']:b for b in math['books']};lock=threading.Lock()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def slug(s):return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')
def log(obj):
 with lock:
  with (BASE/'download_attempts.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(obj,ensure_ascii=False)+'\n')
def fetch(book):
 code=book['book_code'];grade='common_11_12' if book['class_selector']==13 else f"class_{book['class_selector']:02d}";folder=BASE/grade/slug(book['subject'])/code;folder.mkdir(parents=True,exist_ok=True)
 record_path=folder/'acquisition.json'
 if code in maths:
  b=maths[code];archive=MATH/b['archive_relative_path'];assert sha(archive)==b['archive_sha256']
  record={**book,'status':'reused_verified_existing_mathematics','archive_path':str(archive),'archive_sha256':b['archive_sha256'],'archive_bytes':b['archive_bytes'],'existing_volume_manifest':str(archive.parent/'volume_manifest.json'),'existing_reading_copy':str(MATH/b['reading_copy']['relative_path']),'collection_folder':str(folder)}
  write(record_path,record);return record
 archive=folder/(code+'dd.zip');receipt_path=folder/'archive_receipt.json'
 if archive.exists() and receipt_path.exists():
  receipt=json.loads(receipt_path.read_text(encoding='utf-8'));assert sha(archive)==receipt['sha256']
  record={**book,'status':'archive_acquired','archive_path':str(archive),'archive_sha256':receipt['sha256'],'archive_bytes':receipt['bytes'],'collection_folder':str(folder)};write(record_path,record);return record
 assert not archive.exists(),'Unreceipted archive exists; do not replace'
 temp=folder/(code+'.download');header=folder/'download.headers.tmp'
 command=['curl.exe','--silent','--show-error','--location','--fail','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','300','--retry','1','--retry-all-errors','--retry-delay','1','--dump-header',str(header),'--output',str(temp),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}',book['archive_url']]
 if temp.exists() and temp.stat().st_size>0:command[1:1]=['--continue-at','-']
 started=datetime.now(timezone.utc).isoformat();run=subprocess.run(command,capture_output=True,text=True);meta=run.stdout.splitlines()
 if run.returncode:
  record={**book,'status':'archive_download_failed','curl_exit':run.returncode,'error':run.stderr.strip(),'attempted_at_utc':started,'collection_folder':str(folder)};write(record_path,record);log(record);return record
 try:
  assert urllib.parse.urlparse(meta[1]).hostname in {'ncert.nic.in','www.ncert.nic.in'}
  with zipfile.ZipFile(temp) as z:
   assert sum(x.file_size for x in z.infolist())<3_000_000_000,'Excessive uncompressed archive size'
   assert z.testzip() is None,'ZIP CRC failure'
   members=[{'name':x.filename,'bytes':x.file_size,'crc32':format(x.CRC,'08x')} for x in z.infolist() if not x.is_dir()]
  receipt={'requested_url':book['archive_url'],'final_url':meta[1],'http_status':int(meta[0]),'content_type':meta[2],'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'bytes':temp.stat().st_size,'sha256':sha(temp),'zip_crc_check':'passed','members':members,'tls_verification_disabled':False}
  if header.exists():
   h=header.read_text(encoding='utf-8',errors='replace');receipt['last_modified']=re.findall(r'^Last-Modified:\s*(.*)$',h,re.I|re.M);receipt['etag']=re.findall(r'^ETag:\s*(.*)$',h,re.I|re.M)
  temp.rename(archive);write(receipt_path,receipt)
  if header.exists():header.unlink()
  record={**book,'status':'archive_acquired','archive_path':str(archive),'archive_sha256':receipt['sha256'],'archive_bytes':receipt['bytes'],'archive_member_count':len(members),'collection_folder':str(folder)}
 except Exception as e:record={**book,'status':'archive_validation_failed','error':type(e).__name__+': '+str(e),'collection_folder':str(folder)}
 write(record_path,record);log({'book_code':code,'status':record['status'],'bytes':record.get('archive_bytes'),'error':record.get('error'),'at_utc':datetime.now(timezone.utc).isoformat()});return record
if __name__=='__main__':
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(fetch,b):b['book_code'] for b in selection['books']}
  for future in concurrent.futures.as_completed(futures):
   code=futures[future]
   try:r=future.result()
   except Exception as e:r={'book_code':code,'status':'unexpected_error','error':type(e).__name__+': '+str(e)}
   results.append(r);print(json.dumps({'done':len(results),'total':len(futures),'book_code':code,'status':r['status'],'bytes':r.get('archive_bytes'),'error':r.get('error')}),flush=True)
 write(BASE/'download_results.json',sorted(results,key=lambda x:x['book_code']))
 print(json.dumps({'archives_acquired':sum(r['status']=='archive_acquired' for r in results),'math_reused':sum(r['status']=='reused_verified_existing_mathematics' for r in results),'needs_followup':sum(r['status'] not in {'archive_acquired','reused_verified_existing_mathematics'} for r in results)}),flush=True)
