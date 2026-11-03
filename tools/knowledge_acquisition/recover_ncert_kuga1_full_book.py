from pathlib import Path
from datetime import datetime,timezone
import concurrent.futures,hashlib,json,subprocess
base=Path('Directions/ncert_all_subjects_8_12/2026-11-03');book=json.loads(next(base.glob('**/kuga1/acquisition.json')).read_text(encoding='utf-8'));folder=Path(book['collection_folder'])/'official_member_recovery';folder.mkdir(exist_ok=True)
def fetch(name):
 dest=folder/name;receipt_path=dest.with_suffix('.receipt.json');url='https://ncert.nic.in/textbook/pdf/'+name
 if dest.exists() and receipt_path.exists():
  old=json.loads(receipt_path.read_text(encoding='utf-8'));data=dest.read_bytes()
  if old.get('valid_pdf_header') and hashlib.sha256(data).hexdigest()==old['sha256']:return old
 run=subprocess.run(['curl.exe','--silent','--show-error','--location','--fail','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','60','--retry','1','--retry-all-errors','--output',str(dest),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}',url],capture_output=True,text=True);meta=run.stdout.splitlines();data=dest.read_bytes() if dest.exists() else b''
 r={'book_code':'kuga1','filename':name,'requested_url':url,'http_status':meta[0] if meta else None,'final_url':meta[1] if len(meta)>1 else None,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'curl_exit':run.returncode,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'valid_pdf_header':run.returncode==0 and b'%PDF-' in data[:1024],'local_path':str(dest),'curl_stderr':run.stderr.strip() or None}
 receipt_path.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');return r
names=['kuga1ps.pdf']+['kuga1'+f'{i:02d}.pdf' for i in range(1,23)];results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 futures={pool.submit(fetch,n):n for n in names}
 for f in concurrent.futures.as_completed(futures):
  r=f.result();results.append(r);print(json.dumps({'file':r['filename'],'valid_pdf':r['valid_pdf_header'],'bytes':r['bytes'],'http':r.get('http_status')}),flush=True)
(folder/'full_book_downloads.json').write_text(json.dumps(sorted(results,key=lambda r:r['filename']),indent=2)+'\n',encoding='utf-8')
print(json.dumps({'valid_files':sum(r['valid_pdf_header'] for r in results),'expected':23,'missing':[r['filename'] for r in results if not r['valid_pdf_header']]}))
