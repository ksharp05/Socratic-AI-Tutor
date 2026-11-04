from pathlib import Path
from PIL import Image,ImageDraw
import json,os,shutil,subprocess,concurrent.futures,hashlib
root=Path.cwd();base=root/'Directions/ncert_all_subjects_8_12/2026-11-03';qa=base/'qa';qa.mkdir(exist_ok=True)
ids=['hecu1','iesc1','jesc1','keph1','kech1','kebo1','leph1','lech1','lebo1','keac1','lecs1','hees1','iekv1','ihsh1','hhml1','iuju1','khgv1','lstp1','kuga1','hekr1'];binary=Path(os.environ.get('POPPLER_BIN') or Path(shutil.which('pdftoppm') or 'pdftoppm').parent)/'pdftoppm'  # set POPPLER_BIN or put Poppler on PATH
def render(code):
 p=next(base.glob('**/'+code+'/volume_manifest.json'));b=json.loads(p.read_text(encoding='utf-8'));f=next((x for x in b['originals'] if x['name'].lower().endswith('ps.pdf') and x['pdf_parse']!='failed'),None) or next(x for x in b['originals'] if x['pdf_parse']!='failed');dest=qa/(code+'_title')
 run=subprocess.run([str(binary),'-f','1','-l','1','-scale-to','900','-singlefile','-png',f['absolute_path'],str(dest)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30);assert run.returncode==0,run.stderr
 return {'book_code':code,'source_pdf':f['absolute_path'],'source_sha256':f['sha256'],'render_path':str(dest.with_suffix('.png'))}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(render,ids))
for start in range(0,len(results),6):
 group=results[start:start+6];sheet=Image.new('RGB',(1800,1560),'#e5e7eb');draw=ImageDraw.Draw(sheet)
 for i,r in enumerate(group):
  im=Image.open(r['render_path']).convert('RGB');im.thumbnail((580,730));x=(i%3)*600+(600-im.width)//2;y=(i//3)*780+32;sheet.paste(im,(x,y));draw.text(((i%3)*600+12,(i//3)*780+10),r['book_code'],fill='black')
 sheet.save(qa/f'subject_titles_{start//6+1:02d}.png')
(qa/'subject_render_checks.json').write_text(json.dumps({'status':'rendered_pending_visual_inspection','sampled_books':len(results),'renders':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rendered_title_pages':len(results),'contact_sheets':4}))
