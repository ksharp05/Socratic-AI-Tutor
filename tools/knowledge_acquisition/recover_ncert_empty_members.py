from pathlib import Path
from datetime import datetime,timezone
import subprocess,concurrent.futures,json,hashlib
base=Path('Directions/ncert_all_subjects_8_12/2026-11-03');bad=json.loads((base/'invalid_pdf_members_scan.json').read_text(encoding='utf-8'))
def fetch(x):
 folder=Path(x['collection_folder'])/'official_member_recovery';folder.mkdir(exist_ok=True);dest=folder/Path(x['filename']).name;url='https://ncert.nic.in/textbook/pdf/'+dest.name
 run=subprocess.run(['curl.exe','--silent','--show-error','--location','--fail','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','60','--retry','1','--retry-all-errors','--output',str(dest),'--write-out','%{http_code}\n%{url_effective}\n%{content_type}',url],capture_output=True,text=True);meta=run.stdout.splitlines();data=dest.read_bytes() if dest.exists() else b''
 r={**x,'requested_url':url,'http_status':meta[0] if meta else None,'final_url':meta[1] if len(meta)>1 else None,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'curl_exit':run.returncode,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'valid_pdf_header':b'%PDF-' in data[:1024],'local_path':str(dest),'error':run.stderr.strip() or None}
 dest.with_suffix('.receipt.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');return r
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(fetch,bad))
(base/'member_recovery_results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8');print(json.dumps(results,ensure_ascii=False))
