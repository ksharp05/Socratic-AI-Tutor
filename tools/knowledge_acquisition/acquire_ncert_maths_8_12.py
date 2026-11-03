from pathlib import Path
import re,json,hashlib,subprocess,concurrent.futures,zipfile
from datetime import datetime,timezone
root=Path.cwd();base=root/'Directions/ncert_maths_8_12/2026-11-03';s=(base/'catalogue/index.html').read_text(encoding='utf-8')
selected={8:['hegp1','hegp2'],9:['iemh1','iemh2'],10:['jemh1'],11:['kemh1'],12:['lemh1','lemh2']};books=[]
for grade,codes in selected.items():
 start=re.search(r'else if\(\(document\.test\.tclass\.value=='+str(grade)+r'\) && \(document\.test\.tsubject\.options\[sind\]\.text=="Mathematics"\)\)',s)
 assert start,grade
 block=s[start.end():s.find('\n\t}',start.end())]
 for code in codes:
  match=re.search(r'document\.test\.tbook\.options\[(\d+)\]\.text="([^"]+)";\s*document\.test\.tbook\.options\[\1\]\.value="(textbook\.php\?'+code+r'=0-(\d+))"',block)
  assert match,code
  books.append({'class':grade,'book_code':code,'catalogue_title':match[2],'expected_chapter_count':int(match[4]),'catalogue_url':'https://ncert.nic.in/'+match[3],'archive_url':'https://ncert.nic.in/textbook/pdf/'+code+'dd.zip','language':'English','selection_evidence':'official class Mathematics dropdown; English book code/title'})
registry={'collection_date_local':'2026-11-03','timezone':'Asia/Calcutta','catalogue_url':'https://ncert.nic.in/textbook.php','catalogue_file':'catalogue/index.html','catalogue_sha256':hashlib.sha256((base/'catalogue/index.html').read_bytes()).hexdigest(),'books':books}
(base/'book_selection.json').write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
def fetch(book):
 code=book['book_code'];folder=base/f"class_{book['class']:02d}"/code;folder.mkdir(parents=True,exist_ok=True);dest=folder/(code+'dd.zip');receipt_path=folder/'archive_receipt.json'
 if dest.exists() and receipt_path.exists():
  receipt=json.loads(receipt_path.read_text());assert hashlib.sha256(dest.read_bytes()).hexdigest()==receipt['sha256'];return {'book':code,'reused':True,'bytes':dest.stat().st_size}
 assert not dest.exists(),'Existing unreceipted file; do not overwrite'
 temp=dest.with_suffix('.download');headers=folder/'download.headers.tmp'
 cmd=['curl.exe','--silent','--show-error','--location','--fail','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','120','--retry','1','--retry-delay','1','--dump-header',str(headers),'--output',str(temp),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}\n%{size_download}',book['archive_url']]
 run=subprocess.run(cmd,capture_output=True,text=True);meta=run.stdout.splitlines()
 if run.returncode:
  return {'book':code,'error':run.stderr.strip(),'returncode':run.returncode}
 with zipfile.ZipFile(temp) as archive:
  assert archive.testzip() is None,'ZIP CRC failure'
  members=[{'name':x.filename,'bytes':x.file_size,'crc32':format(x.CRC,'08x')} for x in archive.infolist() if not x.is_dir()]
 receipt={'book_code':code,'requested_url':book['archive_url'],'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'http_status':int(meta[0]),'final_url':meta[1],'content_type':meta[2],'bytes':temp.stat().st_size,'sha256':hashlib.sha256(temp.read_bytes()).hexdigest(),'zip_crc_check':'passed','members':members,'tls_verification_disabled':False}
 if headers.exists():
  h=headers.read_text(encoding='utf-8',errors='replace');receipt['last_modified_headers']=re.findall(r'^Last-Modified:\s*(.*)$',h,re.M|re.I);receipt['etag_headers']=re.findall(r'^ETag:\s*(.*)$',h,re.M|re.I)
 temp.rename(dest);receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 return {'book':code,'bytes':receipt['bytes'],'members':len(members),'pdfs':sum(x['name'].lower().endswith('.pdf') for x in members)}
print(json.dumps({'selected_books':books,'expected_chapters':sum(x['expected_chapter_count'] for x in books)}),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 results=[]
 for result in pool.map(fetch,books):results.append(result);print(json.dumps(result),flush=True)
(base/'download_summary.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
raise SystemExit(any('error' in r for r in results))
