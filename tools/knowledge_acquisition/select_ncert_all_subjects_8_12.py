from pathlib import Path
import re,json,hashlib,subprocess
from datetime import datetime,timezone
ROOT=Path.cwd();BASE=ROOT/'Directions/ncert_all_subjects_8_12/2026-11-03';(BASE/'catalogue').mkdir(parents=True,exist_ok=True)
path=BASE/'catalogue/index.html'
if not path.exists() or path.stat().st_size<1000:
 run=subprocess.run(['curl.exe','--silent','--show-error','--location','--fail','--proto','=https','--proto-redir','=https','--connect-timeout','15','--max-time','45','--retry','2','--retry-all-errors','--retry-delay','1','--output',str(path),'https://ncert.nic.in/textbook.php'],capture_output=True,text=True);assert run.returncode==0,run.stderr
html=path.read_text(encoding='utf-8')
def uncomment(s):
 out=[];i=0;quote=None
 while i<len(s):
  c=s[i]
  if quote:
   out.append(c)
   if c=='\\' and i+1<len(s):i+=1;out.append(s[i])
   elif c==quote:quote=None
   i+=1;continue
  if c in '\"\x27`':quote=c;out.append(c);i+=1;continue
  if s[i:i+2]=='//':
   j=s.find('\n',i);i=len(s) if j<0 else j;continue
  if s[i:i+2]=='/*':
   j=s.find('*/',i+2);i=len(s) if j<0 else j+2;continue
  out.append(c);i+=1
 return ''.join(out)
def block_after(text,pos):
 start=text.find('{',pos);depth=0;quote=None;i=start
 assert start>=0
 while i<len(text):
  c=text[i]
  if quote:
   if c=='\\':i+=2;continue
   if c==quote:quote=None
  elif c in '\"\x27`':quote=c
  elif c=='{':depth+=1
  elif c=='}':
   depth-=1
   if not depth:return text[start+1:i]
  i+=1
 raise ValueError('Unclosed source block')
js='\n'.join(uncomment(x) for x in re.findall(r'<script[^>]*>(.*?)</script\s*>',html,re.S|re.I))
menus={}
for grade in range(8,14):
 h=re.search(r'(?:else\s+)?if\s*\(document\.test\.tclass\.value=='+str(grade)+r'\)',js);assert h,grade
 block=block_after(js,h.end());menus[grade]=[title for idx,title in re.findall(r'document\.test\.tsubject\.options\[(\d+)\]\.text\s*=\s*"([^"]*)"',block) if int(idx)>0 and title]
pat=re.compile(r'(?:else\s+)?if\s*\(\(document\.test\.tclass\.value==(\d+)\)\s*&&\s*\(document\.test\.tsubject\.options\[sind\]\.text=="([^"]+)"\)\)')
branches={};inactive=[]
for h in pat.finditer(js):
 grade=int(h[1]);subject=h[2]
 if grade not in menus:continue
 block=block_after(js,h.end());titles=dict(re.findall(r'document\.test\.tbook\.options\[(\d+)\]\.text\s*=\s*"([^"]*)"',block));values=re.findall(r'document\.test\.tbook\.options\[(\d+)\]\.value\s*=\s*"(?:textbook\.php\?)?([A-Za-z0-9]+)=0-(\d+)"',block)
 books=[{'book_code':code,'catalogue_title':titles.get(idx,''),'catalogue_chapter_count':int(n),'catalogue_url':f'https://ncert.nic.in/textbook.php?{code}=0-{n}','archive_url':f'https://ncert.nic.in/textbook/pdf/{code}dd.zip'} for idx,code,n in values]
 if subject not in menus[grade]:inactive.append({'class_selector':grade,'subject':subject,'book_codes':[x['book_code'] for x in books]});continue
 assert (grade,subject) not in branches,(grade,subject)
 branches[(grade,subject)]=books
language_subjects={'English','Hindi','Sanskrit','Urdu','Creative Writing and Translation','Creative Writing & Translation'}
known_nonenglish={'lehh1':'Hindi','lehh2':'Hindi'}
selected=[];excluded=[];gaps=[];groups=[]
for grade,subjects in menus.items():
 for subject in subjects:
  candidates=branches.get((grade,subject),[])
  if not candidates:gaps.append({'class_selector':grade,'subject':subject,'status':'publisher_coming_soon_no_active_book_download' if grade==9 and subject=='ICT' else 'no_book_options_in_active_menu','catalogue_label':'Coming Soon' if grade==9 and subject=='ICT' else None});continue
  english=[b for b in candidates if b['book_code'][1:2]=='e' and b['book_code'] not in known_nonenglish]
  if subject in language_subjects:chosen=candidates;reason='language_subject_all_listed_titles'
  elif english:chosen=english;reason='English_medium_non_language_subject'
  else:chosen=candidates;reason='no_English_option_listed_collect_available_language_titles'
  groups.append({'class_selector':grade,'grades':[11,12] if grade==13 else [grade],'subject':subject,'selected_codes':[b['book_code'] for b in chosen],'catalogue_candidates':len(candidates),'selection_reason':reason})
  for b in candidates:
   row={**b,'class_selector':grade,'grades':[11,12] if grade==13 else [grade],'subject':subject}
   if b in chosen:
    lang=subject if subject in {'English','Hindi','Sanskrit','Urdu'} else ('English' if b in english else ('Hindi' if b['book_code'][1:2]=='h' or subject=='Sangeet' else ('Urdu' if b['book_code'][1:2]=='u' else 'not_yet_confirmed')))
    selected.append({**row,'language_inferred_from_catalogue':lang,'selection_reason':reason})
   else:excluded.append({**row,'reason':'translation_alternative_to_selected_English_title'})
# Deduplicate by official code; preserve every catalogue placement separately.
unique={}
for row in selected:
 code=row['book_code'];placement={k:row[k] for k in ['class_selector','grades','subject']}
 if code not in unique:unique[code]={**row,'catalogue_placements':[placement]}
 else:
  assert unique[code]['catalogue_chapter_count']==row['catalogue_chapter_count'];unique[code]['catalogue_placements'].append(placement)
selection={'date_local':'2026-11-03','timezone':'Asia/Calcutta','catalogue_url':'https://ncert.nic.in/textbook.php','catalogue_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'active class 8-12 subject menus plus active common XI-XII menu; English for non-language subjects; all language-course titles and available-language fallbacks','active_subject_menus':menus,'subject_groups':groups,'books':list(unique.values()),'excluded_translation_options':excluded,'inactive_subject_branches':inactive,'catalogue_gaps':gaps}
(BASE/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for g in groups:
 print(json.dumps({'class':g['class_selector'],'subject':g['subject'],'selected':[(b['book_code'],b['catalogue_title']) for b in unique.values() if b['book_code'] in g['selected_codes']],'reason':g['selection_reason']},ensure_ascii=False))
print(json.dumps({'selected_unique_volumes':len(unique),'subject_groups':len(groups),'chapters_as_catalogued':sum(b['catalogue_chapter_count'] for b in unique.values()),'excluded_translation_options':len(excluded),'inactive_subject_branches':len(inactive),'gaps':gaps}))
