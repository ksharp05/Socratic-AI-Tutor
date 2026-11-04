from pathlib import Path,PurePosixPath
from pypdf import PdfReader
import hashlib,io,json,os,re,shutil,zipfile,concurrent.futures,logging,subprocess
ROOT=Path.cwd();BASE=ROOT/'Directions/ncert_all_subjects_8_12/2026-11-03'
logging.getLogger('pypdf').setLevel(logging.ERROR)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def coverage(book,files):
 code=book['book_code'];numbers=[];notes=[]
 for f in files:
  match=re.fullmatch(re.escape(code)+r'(\d{2})\.+pdf',f['name'],re.I)
  if match:
   numbers.append(int(match[1]))
   if '..pdf' in f['name'].lower():notes.append({'type':'publisher_double_dot_filename','name':f['name'],'logical_index':int(match[1])})
 numbers=sorted(set(numbers));n=book['catalogue_chapter_count'];missing=sorted(set(range(1,n+1))-set(numbers));extra=sorted(set(numbers)-set(range(1,n+1)));flags=[]
 if missing or extra:flags.append({'type':'catalogue_vs_archive_numbering_difference','catalogue_count':n,'observed_numbered_pdf_count':len(numbers),'missing_assuming_contiguous_sequence':missing,'extra_indices_beyond_catalogue_count':extra,'note':'Counts/filenames are not a table-of-contents completeness proof. Inspect publisher contents.'})
 if not any(f['name'].lower()==code+'ps.pdf' for f in files):flags.append({'type':'standard_prelims_filename_not_in_archive'})
 return numbers,flags,notes

def native_fallback(path,expected_pages,folder):
 binary=Path(os.environ.get('POPPLER_BIN') or Path(shutil.which('pdftoppm') or 'pdftoppm').parent)  # set POPPLER_BIN or put Poppler on PATH
 info=subprocess.run([str(binary/'pdfinfo.exe'),str(path)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30);assert info.returncode==0,info.stderr
 n=int(re.search(r'^Pages:\s+(\d+)',info.stdout,re.M)[1]);assert n==expected_pages
 rendered=folder/'verification_renders'/path.stem;rendered.mkdir(parents=True,exist_ok=True)
 run=subprocess.run([str(binary/'pdftoppm.exe'),'-scale-to','600','-png',str(path),str(rendered/'page')],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60);assert run.returncode==0,run.stderr
 pages=sorted(rendered.glob('page-*.png'));assert len(pages)==n
 return {'method':'independent_poppler_pdfinfo_and_all_pages_rendered','pages':n,'rendered_pages':[str(x) for x in pages],'pypdf_safety_limit_retained':True}

def verify(path):
 b=json.loads(path.read_text(encoding='utf-8'));code=b['book_code'];folder=path.parent;target=folder/'volume_manifest.json'
 if b['status'] not in {'archive_acquired','reused_verified_existing_mathematics'}:return {'book_code':code,'status':'acquisition_pending'}
 if target.exists():
  previous=json.loads(target.read_text(encoding='utf-8'))
  if previous.get('archive_sha256')==b['archive_sha256'] and (previous.get('pdf_integrity_errors')==[] or previous.get('source_mode')=='official_individual_PDF_recovery_of_defective_archive'):
   assert all(Path(x['absolute_path']).is_file() and sha(Path(x['absolute_path']))==x['sha256'] for x in previous['originals']), 'Cached source bytes changed'
   numbers,computed_flags,notes=coverage(b,previous['originals']);flags=previous.get('coverage_flags',computed_flags)
   status='known_partial_publisher_defect' if previous.get('pdf_integrity_errors') else 'already_verified'
   return {'book_code':code,'status':status,'pdfs':sum(f['pdf_parse']!='failed' for f in previous['originals']),'pages':previous['source_pages'],'flags':flags}
 archive=Path(b['archive_path']);assert sha(archive)==b['archive_sha256']
 if b['status']=='reused_verified_existing_mathematics':
  old_path=Path(b['existing_volume_manifest']);old=json.loads(old_path.read_text(encoding='utf-8'));old_base=old_path.parents[2]
  files=[]
  for x in old['originals']:
   p=old_base/x['relative_path'];assert p.is_file() and sha(p)==x['sha256'];files.append({**x,'absolute_path':str(p)})
  flags=[];errors=[];numbers=list(range(1,b['catalogue_chapter_count']+1))
 else:
  original_folder=folder/'original_pdfs';original_folder.mkdir(exist_ok=True);files=[];errors=[];flags=[];numbered={};seen={}
  with zipfile.ZipFile(archive) as z:
   for member in z.infolist():
    if member.is_dir() or not member.filename.lower().endswith('.pdf') or member.filename.startswith('__MACOSX/'):continue
    posix=PurePosixPath(member.filename.replace('\\','/'))
    assert not posix.is_absolute() and '..' not in posix.parts and ':' not in member.filename,'Unsafe ZIP PDF path'
    rawname=posix.name;safe=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',rawname)
    if safe.lower() in seen:
     safe=hashlib.sha256(member.filename.encode()).hexdigest()[:10]+'_'+safe
    seen[safe.lower()]=member.filename;dest=original_folder/safe;assert BASE.resolve() in dest.resolve().parents
    data=z.read(member);archive_member_sha256=hashlib.sha256(data).hexdigest();recovery_receipt=None
    if b'%PDF-' not in data[:1024]:
     recovery=folder/'official_member_recovery'/rawname
     receipt_path=recovery.with_suffix('.receipt.json')
     if recovery.exists() and receipt_path.exists():
      recovery_receipt=json.loads(receipt_path.read_text(encoding='utf-8'));data=recovery.read_bytes()
      assert recovery_receipt['valid_pdf_header'] and hashlib.sha256(data).hexdigest()==recovery_receipt['sha256']
      dest=recovery
     else:raise ValueError(f'{member.filename}: invalid original PDF and no verified official recovery')
    h=hashlib.sha256(data).hexdigest()
    if dest.exists():assert dest.read_bytes()==data,'Refusing to replace original PDF bytes'
    else:dest.write_bytes(data)
    rec={'archive_member_original_sha256':archive_member_sha256,'official_recovery_receipt':recovery_receipt,'name':rawname,'archive_member':member.filename,'absolute_path':str(dest),'bytes':len(data),'sha256':h,'pdf_parse':'pending','source_url_candidate':'https://ncert.nic.in/textbook/pdf/'+rawname,'source_url_evidence':'member came from official ZIP; individual URL not separately fetched'}
    try:
     reader=PdfReader(io.BytesIO(data));assert len(reader.pages)>0;rec['pages']=len(reader.pages)
     hashes=[]
     for page in reader.pages:
      assert float(page.mediabox.width)>0 and float(page.mediabox.height)>0
      content=page.get_contents();hashes.append(hashlib.sha256(content.get_data() if content is not None else b'').hexdigest())
     rec.update(pdf_parse='passed',pages=len(reader.pages),source_encryption_present=reader.is_encrypted,readable_without_supplied_password=True,page_content_sha256=hashes)
     try:
      text='\n'.join((page.extract_text() or '') for page in list(reader.pages)[:2]);rec['edition_markers_sampled_first_two_pages']=sorted(set(re.findall(r'(?:Reprint|Reprinted)\s+20\d\d\s*[-–]\s*\d{2,4}',text,re.I)));rec['title_text_sample_private']=' '.join(text[:260].split())
     except Exception as e:rec['metadata_extraction_error']=type(e).__name__
    except Exception as e:
     rec['pdf_parse']='failed';rec['error']=type(e).__name__+': '+str(e)
     if type(e).__name__=='LimitReachedError':
      try:
       rec['alternate_validation']=native_fallback(dest,rec['pages'],folder);rec['pdf_parse']='passed_poppler_fallback';rec['pypdf_bounded_decode_error']=rec.pop('error')
      except Exception as other:rec['alternate_validation_error']=type(other).__name__+': '+str(other)
     if rec['pdf_parse']=='failed':errors.append({'name':rawname,'error':rec['error']})
    files.append(rec)
    match=re.fullmatch(re.escape(code)+r'(\d{2})\.pdf',rawname,re.I)
    if match:numbered[int(match[1])]=rawname
  numbers=sorted(numbered);n=b['catalogue_chapter_count'];missing=sorted(set(range(1,n+1))-set(numbers));extra=sorted(set(numbers)-set(range(1,n+1)))
  if missing or extra:flags.append({'type':'catalogue_vs_archive_numbering_difference','catalogue_count':n,'observed_numbered_pdf_count':len(numbers),'missing_assuming_contiguous_sequence':missing,'extra_indices_beyond_catalogue_count':extra,'note':'Catalogue counts can be stale or numbering can be non-contiguous. Must inspect publisher contents before declaring absent chapters.'})
  if not any(x['name'].lower()==code+'ps.pdf' for x in files):flags.append({'type':'standard_prelims_filename_not_in_archive'})
  if not files:errors.append({'error':'No PDF files in official archive'})
 numbers,flags,filename_notes=coverage(b,files)
 record={**b,'filename_notes':filename_notes,'status':'source_files_verified' if not errors else 'source_pdf_errors','source_pages':sum(f.get('pages',0) for f in files),'pdf_count':len(files),'observed_numbered_pdf_indices':numbers,'coverage_flags':flags,'pdf_integrity_errors':errors,'originals':files,'verification_scope':'SHA-256 and ZIP member CRC; PDF parse, page boxes and page content decoding, with explicitly recorded independent all-page Poppler rendering for bounded-parser exceptions. No teaching-quality or universal mathematical-correctness claim.','not_approved_for_tutor_ingestion':True}
 save(target,record);return {'book_code':code,'status':record['status'],'pdfs':len(files),'pages':record['source_pages'],'flags':flags,'errors':errors}
if __name__=='__main__':
 paths=list(BASE.glob('**/acquisition.json'));results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(verify,p):p.parent.name for p in paths}
  for future in concurrent.futures.as_completed(futures):
   code=futures[future]
   try:r=future.result()
   except Exception as e:r={'book_code':code,'status':'verifier_error','error':type(e).__name__+': '+str(e)}
   results.append(r)
   if r['status'] not in {'already_verified','acquisition_pending'}:print(json.dumps(r,ensure_ascii=False),flush=True)
 save(BASE/'verification_pass.json',results)
 print(json.dumps({'scanned_records':len(paths),'verified_or_reused':sum(r['status'] in {'source_files_verified','already_verified'} for r in results),'needs_followup':sum(r['status'] in {'verifier_error','source_pdf_errors','known_partial_publisher_defect'} for r in results),'numbering_flags':sum(bool(r.get('flags')) for r in results)}),flush=True)
