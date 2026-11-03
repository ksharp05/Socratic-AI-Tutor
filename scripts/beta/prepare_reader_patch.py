from pathlib import Path
import sqlite3,json,sys
root=Path.cwd();sys.path.insert(0,str(root/'src'))
from socrates_beta.knowledge import normalize_quote
with sqlite3.connect(root/'Directions/book_pipeline/v0_1/staff_pages.sqlite') as c:
 meta=json.loads(c.execute("select metadata from sources where id='jeff1/jeff101.pdf'").fetchone()[0]);raw=c.execute("select text from pages where source_id='jeff1/jeff101.pdf' and page=1").fetchone()[0]
page=normalize_quote(raw);start=page.index('Lencho is a farmer');end=page.index('a hundred pesos.',start)+len('a hundred pesos.')
r={'id':'ncert:reader_lencho_intro','grades':[10],'subject':'English','book':'jeff1','title':'A Letter to God — Lencho and faith',
 'text':page[start:end],'page':1,'unit_file_index':1,'source_file':meta['path'],'source_sha256':meta['sha256'],
 'source_url':meta['source_url'],'source_id':meta['source_id']}
(root/'Directions/beta_data/imports/ncert-primary-reader-recovery.jsonl').write_text(json.dumps(r,ensure_ascii=False)+'\n',encoding='utf-8')
print('Prepared exact primary-reader quote, source page 1')
