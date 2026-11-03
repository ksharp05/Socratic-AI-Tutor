from __future__ import annotations
import json,sqlite3,shutil
from pathlib import Path
from ncert_pipeline.catalogue import read_json,sha256
from ncert_pipeline.build import insert_passage
from .headings import chapter_title
from .knowledge import DatasetRegistry,import_jsonl,normalize_quote,database

DEFAULT_ID='ncert-2026-11-03-beta2'


def bootstrap(root: Path,app_root: Path,data_directory=None):
    data=Path(data_directory) if data_directory else root/'Directions/beta_data';registry=DatasetRegistry(data)
    # An explicitly registered active version is sufficient; it need not be the historical default.
    # Verify its recorded hash before accepting it. Never rebuild or replace registered data.
    if registry.entries().get('active'):
        registry.knowledge()
        return registry
    original=root/'Directions/book_pipeline/v0_1';report=read_json(original/'BUILD_REPORT.json')
    for name in ('preview.sqlite','staff_pages.sqlite'):
        if sha256(original/name)!=report['outputs'][name]:raise ValueError('Original extraction index differs from its receipt')
    folder=data/'datasets'/DEFAULT_ID;folder.mkdir(parents=True,exist_ok=True)
    target=folder/'knowledge.sqlite'
    if target.exists():raise ValueError('Unregistered beta build exists; inspect before overwriting')
    staging=folder/'knowledge.building.sqlite'
    if staging.exists():raise ValueError('Unfinished beta build exists')
    shutil.copy2(original/'preview.sqlite',staging)
    with database(original/'staff_pages.sqlite') as raw:
        source=json.loads(raw.execute('SELECT metadata FROM sources WHERE id=?',('hecu1/hecu105.pdf',)).fetchone()[0])
        page=normalize_quote(raw.execute('SELECT text FROM pages WHERE source_id=? AND page=7',('hecu1/hecu105.pdf',)).fetchone()[0])
    start=page.index('Friction arises due to the irregularities')
    end=page.index('any effort to move one surface over the other.',start)+len('any effort to move one surface over the other.')
    patch={'id':'ncert:beta_friction_irregularities','grades':[8],'subject':'Science','book':'hecu1',
       'title':'Exploring Forces — Friction','text':page[start:end],'page':7,'unit_file_index':5,
       'source_file':source['path'],'source_sha256':source['sha256'],'source_url':source['source_url'],'source_id':source['source_id']}
    imports=data/'imports';imports.mkdir(exist_ok=True)
    patch_file=imports/'ncert-friction-recovery.jsonl';patch_file.write_text(json.dumps(patch,ensure_ascii=False)+'\n',encoding='utf-8')
    patch_index=folder/'recovery.sqlite';import_jsonl(patch_file,patch_index)
    with database(staging) as c, database(patch_index) as patch_db:
        patch_db.row_factory=sqlite3.Row
        for p in patch_db.execute('SELECT * FROM passages'):
            d=dict(p);grades=[r[0] for r in patch_db.execute('SELECT grade FROM scopes WHERE passage_id=?',(d['id'],))]
            insert_passage(c,d,grades)
        c.execute('CREATE TABLE readings(book TEXT,unit INTEGER,title TEXT,source_id TEXT,PRIMARY KEY(book,unit))')
        with database(original/'staff_pages.sqlite') as staff:
            for sid,metadata,text in staff.execute('SELECT s.id,s.metadata,p.text FROM sources s JOIN pages p ON p.source_id=s.id WHERE p.page=1'):
                meta=json.loads(metadata)
                if meta['language']!='English' or meta['unit_file_index'] is None:continue
                heading=chapter_title(text)
                if heading:c.execute('INSERT INTO readings VALUES (?,?,?,?)',(meta['book'],meta['unit_file_index'],heading,sid))
        c.execute('CREATE TABLE concepts(id TEXT PRIMARY KEY,title TEXT,description TEXT,prerequisites TEXT,unit INTEGER,passage_ids TEXT)')
        concepts=app_root/'content/dataset-v0.10.0/concepts.jsonl'
        for line in concepts.read_text(encoding='utf-8-sig').splitlines():
            x=json.loads(line)
            if not c.execute('SELECT 1 FROM passages WHERE id=?',('normalized:'+x['concept_id'],)).fetchone():raise ValueError('Concept has no registered reference')
            unit={'quadratic_equations':4,'arithmetic_progressions':5,'introduction_to_trigonometry':8}.get(x['chapter'])
            if unit is None:unit=8 if x['concept_id'].startswith('tr') else None
            c.execute('INSERT INTO concepts VALUES (?,?,?,?,?,?)',(x['concept_id'],x['title'],x['explanation'],json.dumps(x['prerequisites']),unit,json.dumps(x['supporting_passage_ids'])))
        c.execute('INSERT INTO metadata VALUES (?,?)',('beta_augmentation',json.dumps({'original_index_sha256':sha256(original/'preview.sqlite'),
          'recovery_jsonl_sha256':sha256(patch_file),'concepts_sha256':sha256(concepts),'review_status':'pending'})))
    staging.replace(target)
    registry.register(DEFAULT_ID,target,title='NCERT Classes 8–12 · English beta',activate=True,
        provenance={'base_manifest_sha256':report['manifest_sha256'],'recovered_passages':1,'human_approvals':0})
    return registry
