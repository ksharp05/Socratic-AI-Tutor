from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
from pypdf import PdfReader,PdfWriter
import hashlib,io,json,re,zipfile,subprocess,concurrent.futures
ROOT=Path.cwd();BASE=ROOT/'Directions/ncert_maths_8_12/2026-11-03'
def digest(data):return hashlib.sha256(data).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
NAMES={'hegp1':'NCERT_Class_08_Ganita_Prakash_Part_I','hegp2':'NCERT_Class_08_Ganita_Prakash_Part_II','iemh1':'NCERT_Class_09_Ganita_Manjari_Part_I','iemh2':'NCERT_Class_09_Ganita_Manjari_Part_II','jemh1':'NCERT_Class_10_Mathematics','kemh1':'NCERT_Class_11_Mathematics','lemh1':'NCERT_Class_12_Mathematics_Part_I','lemh2':'NCERT_Class_12_Mathematics_Part_II'}
selection=json.loads((BASE/'book_selection.json').read_text(encoding='utf-8'));books=[]
for book in selection['books']:
 code=book['book_code'];folder=BASE/f"class_{book['class']:02d}"/code;archive=folder/(code+'dd.zip');receipt=json.loads((folder/'archive_receipt.json').read_text(encoding='utf-8'))
 assert digest(archive.read_bytes())==receipt['sha256']
 original_folder=folder/'original_pdfs';original_folder.mkdir(exist_ok=True);files=[]
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  names=[n for n in z.namelist() if n.lower().endswith('.pdf') and not n.startswith('__MACOSX/')]
  basenames=[PurePosixPath(n).name.lower() for n in names];assert len(basenames)==len(set(basenames))
  expected={code+f'{n:02d}.pdf' for n in range(1,book['expected_chapter_count']+1)}
  numbered={n for n in basenames if re.fullmatch(re.escape(code)+r'\d\d\.pdf',n)};assert numbered==expected,(code,expected-numbered,numbered-expected)
  assert code+'ps.pdf' in basenames
  for member in names:
   safe=PurePosixPath(member);assert not safe.is_absolute() and '..' not in safe.parts and '\\' not in member
   name=safe.name.lower();assert re.fullmatch(re.escape(code)+r'(?:\d\d|ps|a1|a2|an|sm)\.pdf',name),name
   data=z.read(member);assert data.startswith(b'%PDF-');path=original_folder/name
   if path.exists():assert path.read_bytes()==data,'Refusing to replace original source bytes'
   else:path.write_bytes(data)
   reader=PdfReader(io.BytesIO(data));assert len(reader.pages)>0
   page_hashes=[]
   for page in reader.pages:
    assert float(page.mediabox.width)>0 and float(page.mediabox.height)>0
    content=page.get_contents();page_hashes.append(digest(content.get_data() if content is not None else b''))
   sampled='\n'.join((p.extract_text() or '') for p in list(reader.pages)[:3])
   markers=sorted(set(re.findall(r'Reprint\s+20\d\d\s*[-–]\s*\d{2,4}',sampled,re.I)))
   edition=[]
   if name.endswith('ps.pdf'):
    lines=sampled.splitlines()
    for i,line in enumerate(lines):
     if re.fullmatch(r'\s*(?:First Edition|Revised Edition)\s*',line,re.I):edition.append(' '.join(lines[i:i+3]).strip()[:150])
   files.append({'name':name,'archive_member':member,'source_url':'https://ncert.nic.in/textbook/pdf/'+name,'relative_path':path.relative_to(BASE).as_posix(),'bytes':len(data),'sha256':digest(data),'pages':len(reader.pages),'page_content_sha256':page_hashes,'edition_markers_sampled_first_three_pages':markers,'edition_statements_from_prelims':edition,'pdf_parse':'passed','source_encryption_present':reader.is_encrypted,'readable_without_supplied_password':True,'all_page_content_streams_decoded':True})
 # The official ZIP order is not reading order. Preserve prelims and chapter order;
 # appendices and supplementary material precede the answers section.
 def order(record):
  suffix=record['name'][len(code):-4]
  if suffix=='ps':return (0,0)
  if suffix.isdigit():return (1,int(suffix))
  return (2,{'a1':1,'a2':2,'sm':3,'an':4}[suffix])
 files.sort(key=order);writer=PdfWriter();page_map=[]
 for record in files:
  start=len(writer.pages)+1;writer.append(str(BASE/record['relative_path']),import_outline=False)
  label=record['name'][len(code):-4];label='Prelims' if label=='ps' else ('Chapter '+str(int(label)+{'iemh2':8,'lemh2':6}.get(code,0)) if label.isdigit() else {'a1':'Appendix I','a2':'Appendix II','sm':'Supplementary material','an':'Answers'}[label])
  writer.add_outline_item(label,start-1)
  page_map.append({'original_file':record['name'],'navigation_label':label,'assembled_first_page_1based':start,'assembled_last_page_1based':len(writer.pages),'source_sha256':record['sha256']})
 writer.add_metadata({'/Title':NAMES[code].replace('_',' '),'/Subject':'Locally assembled reading copy from official NCERT chapter PDFs. Original PDFs and ZIP retained unchanged.','/Producer':'Socratic Tutor local acquisition; pypdf'})
 target=folder/(NAMES[code]+'.pdf');temporary=target.with_suffix('.assembling.pdf')
 with temporary.open('wb') as stream:writer.write(stream)
 writer.close();combined=PdfReader(temporary);expected_hashes=[h for f in files for h in f['page_content_sha256']]
 assert len(combined.pages)==len(expected_hashes)
 for page,expected_hash in zip(combined.pages,expected_hashes):
  content=page.get_contents();assert digest(content.get_data() if content is not None else b'')==expected_hash,'Page content stream changed during assembly'
 temp_bytes=temporary.read_bytes()
 if target.exists():
  if target.read_bytes()!=temp_bytes:
   previous=json.loads((folder/'volume_manifest.json').read_text(encoding='utf-8'))
   assert digest(target.read_bytes())==previous['reading_copy']['sha256'],'Refusing to replace an unrecognized reading copy'
   assert BASE.resolve() in target.resolve().parents
   temporary.replace(target)
  else:temporary.unlink()
 else:temporary.rename(target)
 record={**book,'archive_relative_path':archive.relative_to(BASE).as_posix(),'archive_sha256':receipt['sha256'],'archive_bytes':receipt['bytes'],'retrieved_at_utc':receipt['retrieved_at_utc'],'final_download_url':receipt['final_url'],'original_pdf_count':len(files),'original_pages':sum(f['pages'] for f in files),'missing_chapters':[],'originals':files,'reading_copy':{'relative_path':target.relative_to(BASE).as_posix(),'sha256':digest(temp_bytes),'bytes':len(temp_bytes),'pages':len(combined.pages),'origin':'locally_assembled_from_official_unchanged_pdf_members','is_official_single_file_download':False,'all_page_content_streams_match_originals':True,'page_map':page_map},'not_approved_for_tutor_ingestion':True}
 save(folder/'volume_manifest.json',record);books.append(record)
 print(json.dumps({'book':code,'pdfs':len(files),'chapters':len(expected),'pages':record['original_pages'],'assembled_page_streams_match':True}),flush=True)
manifest={'collection_date_local':'2026-11-03','timezone':'Asia/Calcutta','status':'all_official_catalogue_volumes_acquired_and_pdf_integrity_checked','official_catalogue_url':selection['catalogue_url'],'catalogue_sha256':selection['catalogue_sha256'],'language':'English','classes':[8,9,10,11,12],'volume_count':len(books),'chapter_count':sum(b['expected_chapter_count'] for b in books),'original_pdf_count':sum(b['original_pdf_count'] for b in books),'original_page_count':sum(b['original_pages'] for b in books),'official_archive_bytes':sum(b['archive_bytes'] for b in books),'missing_volumes':[],'missing_chapters':[],'source_pdfs_modified':False,'tutor_runtime_changed':False,'human_review_claimed':False,'pdf_validation_scope':'ZIP CRC; PDF parse and positive page dimensions; decode every page content stream; hash original bytes; assembled-page content stream hashes match originals. This does not certify all mathematics or full source layout.','books':books}
save(BASE/'MANIFEST.json',manifest)
print(json.dumps({k:v for k,v in manifest.items() if k!='books'}),flush=True)
