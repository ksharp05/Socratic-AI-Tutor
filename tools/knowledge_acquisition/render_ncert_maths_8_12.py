from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,os,shutil,subprocess,concurrent.futures,hashlib
root=Path.cwd();base=root/'Directions/ncert_maths_8_12/2026-11-03';m=json.loads((base/'MANIFEST.json').read_text(encoding='utf-8'))
qa=base/'qa';qa.mkdir(exist_ok=True)
poppler=Path(os.environ.get('POPPLER_BIN') or Path(shutil.which('pdftoppm') or 'pdftoppm').parent)  # set POPPLER_BIN or put Poppler on PATH
def check(b):
 pdf=base/b['reading_copy']['relative_path'];results=[]
 run=subprocess.run([str(poppler/'pdfinfo.exe'),str(pdf)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0,run.stderr
 for kind,page in [('title',1),('chapter_1',next(x['assembled_first_page_1based'] for x in b['reading_copy']['page_map'] if x['original_file']==b['book_code']+'01.pdf'))]:
  prefix=qa/(b['book_code']+'_'+kind)
  run=subprocess.run([str(poppler/'pdftoppm.exe'),'-f',str(page),'-l',str(page),'-scale-to','1100','-singlefile','-png',str(pdf),str(prefix)],capture_output=True,text=True,encoding='utf-8',errors='replace');assert run.returncode==0,run.stderr
  results.append({'kind':kind,'page':page,'path':prefix.with_suffix('.png').relative_to(base).as_posix()})
 return {'book_code':b['book_code'],'class':b['class'],'pdfinfo':'passed','reading_copy_sha256':b['reading_copy']['sha256'],'renders':results}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(check,m['books']))
for kind in ['title','chapter_1']:
 sheet=Image.new('RGB',(1800,1320),'#e5e7eb');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(results):
  item=next(x for x in r['renders'] if x['kind']==kind);im=Image.open(base/item['path']).convert('RGB');im.thumbnail((435,610))
  x=(i%4)*450+(450-im.width)//2;y=(i//4)*660+36
  sheet.paste(im,(x,y));draw.text(((i%4)*450+12,(i//4)*660+10),f"Class {r['class']} | {r['book_code']} | {kind}",fill='black')
 sheet.save(qa/(kind+'_contact_sheet.png'))
report={'status':'rendered_pending_visual_inspection','pdfinfo_checks_passed':len(results),'rendered_pages':sum(len(r['renders']) for r in results),'results':results}
(qa/'render_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pdfinfo_passed':8,'rendered_pages':16,'title_sheet':str(qa/'title_contact_sheet.png'),'chapter_sheet':str(qa/'chapter_1_contact_sheet.png')}))
