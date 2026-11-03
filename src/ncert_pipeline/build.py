from __future__ import annotations
import concurrent.futures, hashlib, json, os, sqlite3, subprocess, time
from collections import Counter
from pathlib import Path
from .catalogue import load_sources, read_json, sha256
from .content import concept_chunks, page_quality

SCHEMA = '''
CREATE TABLE passages(id TEXT PRIMARY KEY, source_id TEXT, book TEXT, subject TEXT,
 title TEXT, page INTEGER, unit_file_index INTEGER, kind TEXT, text TEXT,
 source_sha256 TEXT, source_url TEXT, human_review_status TEXT, approved INTEGER DEFAULT 0);
CREATE TABLE scopes(passage_id TEXT, grade INTEGER, subject TEXT);
CREATE INDEX scope_index ON scopes(grade,subject,passage_id);
CREATE VIRTUAL TABLE search USING fts5(passage_id UNINDEXED, text, title, tokenize='unicode61');
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT);
'''


def insert_passage(conn, p, grades):
    keys = ('id','source_id','book','subject','title','page','unit_file_index','kind',
            'text','source_sha256','source_url','human_review_status')
    conn.execute('INSERT INTO passages ('+','.join(keys)+') VALUES ('+','.join('?' for _ in keys)+')',
                 [p[k] for k in keys])
    conn.execute('INSERT INTO search(passage_id,text,title) VALUES (?,?,?)',
                 (p['id'],p['text'],p['title']))
    conn.executemany('INSERT INTO scopes VALUES (?,?,?)',
                     [(p['id'],g,p['subject'].casefold()) for g in grades])


def extract(source, tool: Path, cache: Path, tool_sha: str):
    key = hashlib.sha256((source.sha256 + tool_sha).encode()).hexdigest()
    file = cache / (key + '.json')
    if file.exists():
        data = read_json(file)
        if (data.get('source_sha256') == source.sha256 and data.get('extractor_sha256') == tool_sha
                and len(data.get('pages', [])) == source.pages
                and data.get('text_sha256') == hashlib.sha256(json.dumps(data['pages'],ensure_ascii=False).encode()).hexdigest()):
            return data['pages'], True, data.get('encoding_recovery')
    result = subprocess.run([str(tool), '-layout', '-enc', 'UTF-8', source.path, '-'],
                            capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise RuntimeError(f'pdftotext_exit_{result.returncode}')
    recovery = None
    try:
        text = result.stdout.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        # Poppler 4 can emit invalid UTF-8 for damaged font mappings. Retain exact bytes.
        binary = cache / (key + '.extractor_stdout.bin')
        binary.write_bytes(result.stdout)
        text = result.stdout.decode('utf-8', errors='replace')
        recovery = {'source_id':source.source_id,'method':'utf8_replacement_for_text_only',
                    'replacement_characters':text.count('\ufffd'),
                    'raw_output_file':binary.name,'raw_output_sha256':sha256(binary)}
    pages = text.split('\f')
    if pages and not pages[-1].strip():
        pages.pop()
    if len(pages) != source.pages:
        raise ValueError(f'page_count_mismatch:{len(pages)}_vs_{source.pages}')
    data = {'encoding_recovery':recovery,'source_sha256':source.sha256, 'extractor_sha256':tool_sha, 'pages':pages,
            'text_sha256':hashlib.sha256(json.dumps(pages,ensure_ascii=False).encode()).hexdigest()}
    temporary = file.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    os.replace(temporary,file)
    return pages, False, recovery


def import_cards(conn, file: Path, sources):
    by_sha = {s.sha256:s for s in sources}
    count = 0
    for line in file.read_text(encoding='utf-8-sig').splitlines():
        card = json.loads(line)
        a = card['source_anchor']
        s = by_sha.get(a['source_sha256'])
        if s is None or not 1 <= a['source_pdf_page'] <= s.pages:
            raise ValueError('Normalized card has no matching source/page in this collection')
        if card['content_type'] != 'normalized_reference' or card['class'] != 10:
            raise ValueError('Unexpected math reference type')
        p = dict(id=card['passage_id'],source_id=s.source_id,book=s.book,subject=s.subject,
                 title=card['title'],page=a['source_pdf_page'],unit_file_index=s.unit_file_index,
                 kind='normalized_math_reference',text=card['text'],source_sha256=s.sha256,
                 source_url=a['source_url'],human_review_status=card['human_review_status'])
        insert_passage(conn,p,s.grades); count += 1
    return count


def build(root: Path, manifest: Path, output: Path, tool: Path, cards: Path | None, workers=4):
    started = time.monotonic()
    root, output = root.resolve(strict=True), output.resolve()
    if not output.is_relative_to(root / 'Directions' / 'book_pipeline'):
        raise ValueError('Build output must stay in the ignored Directions/book_pipeline directory')
    if not tool.is_file():
        raise ValueError('An explicit working pdftotext executable is required')
    output.mkdir(parents=True,exist_ok=True)
    # Immutable source caches can be reused; each build database is written to staging.
    cache = output / 'text_cache'; cache.mkdir(exist_ok=True)
    sources, receipt = load_sources(manifest,root)
    tool_sha = sha256(tool)
    tool_version = subprocess.run([str(tool),'-v'],capture_output=True,timeout=10)
    receipt.update(extractor={'path':str(tool),'sha256':tool_sha,
                   'version':(tool_version.stderr+tool_version.stdout).decode(errors='replace').splitlines()[:1]},
                   pipeline_version='0.1.0', preview_only=True, human_approvals=0,
                   raw_math_formulas_admitted=False, retrieval='sqlite_fts5_lexical',
                   normalized_cards_sha256=sha256(cards) if cards else None)
    rawpath, indexpath = output/'staff_pages.building.sqlite', output/'preview.building.sqlite'
    for p in (rawpath,indexpath):
        if p.exists(): p.unlink()  # Exact staging files within the validated output directory.
    raw, idx = sqlite3.connect(rawpath), sqlite3.connect(indexpath)
    raw.executescript('CREATE TABLE sources(id TEXT PRIMARY KEY,metadata TEXT);'
                      'CREATE TABLE pages(source_id TEXT,page INTEGER,text TEXT,quality TEXT,PRIMARY KEY(source_id,page));')
    idx.executescript(SCHEMA)
    counters, failures, scope_counts = Counter(), [], Counter()
    encoding_warnings = []

    def job(s):
        try:
            pages, cached, recovery = extract(s,tool,cache,tool_sha)
            return s,pages,cached,None,recovery
        except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
            return s,[],False,type(exc).__name__+':'+str(exc)[:160],None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(workers,8))) as pool:
            for n,(s,pages,cached,error,recovery) in enumerate(pool.map(job,sources),1):
                if error:
                    failures.append({'source_id':s.source_id,'error':error}); continue
                if recovery: encoding_warnings.append(recovery)
                raw.execute('INSERT INTO sources VALUES (?,?)',(s.source_id,json.dumps(s.dict(),ensure_ascii=False)))
                raw.executemany('INSERT INTO pages VALUES (?,?,?,?)',
                     [(s.source_id,i,t,page_quality(t)) for i,t in enumerate(pages,1)])
                counters['sources_extracted'] += 1; counters['pages_extracted'] += len(pages)
                counters['cache_hits'] += int(cached)
                for chunk,stats in concept_chunks(pages,subject=s.subject,language=s.language,
                                                 numbered_asset=s.unit_file_index is not None):
                    if chunk is None:
                        counters.update(stats); break
                    pid = 'ncert:'+hashlib.sha256((s.source_id+s.sha256+str(chunk['page'])+':'+str(chunk['ordinal'])+chunk['text']).encode()).hexdigest()[:24]
                    p = dict(id=pid,source_id=s.source_id,book=s.book,subject=s.subject,
                             title=s.title+(' — '+chunk['heading'] if chunk['heading'] else ''),
                             page=chunk['page'],unit_file_index=s.unit_file_index,kind=chunk['kind'],
                             text=chunk['text'],source_sha256=s.sha256,source_url=s.source_url,
                             human_review_status='pending')
                    insert_passage(idx,p,s.grades)
                    counters['prose_passages'] += 1
                    for g in s.grades: scope_counts[(g,s.subject)] += 1
                if n % 100 == 0:
                    raw.commit(); idx.commit()
                    print(f'Extracted {n}/{len(sources)} assets; {counters["pages_extracted"]} pages; {counters["prose_passages"]} prose candidates',flush=True)
        counters['normalized_math_references'] = import_cards(idx,cards,sources) if cards else 0
        # A machine-generated remediation queue, not human labels or approval.
        by_id = {s.source_id:s for s in sources}
        queue_counts = Counter()
        with (output/'SOURCE_QUALITY_QUEUE.jsonl').open('w',encoding='utf-8') as q:
            for sid,page,quality in raw.execute('SELECT source_id,page,quality FROM pages ORDER BY source_id,page'):
                source = by_id[sid]
                reason = ('language_pipeline_pending' if source.language!='English' else
                          'math_normalization_pending' if source.subject=='Mathematics' else
                          quality if quality!='candidate_english_text' else None)
                if reason:
                    queue_counts[reason] += 1
                    q.write(json.dumps({'source_id':sid,'pdf_page':page,'source_sha256':source.sha256,
                             'reason':reason,'human_review_status':'pending'})+'\n')
        preview_books = {r[0] for r in idx.execute('SELECT DISTINCT book FROM passages')}
        receipt.update(preview_book_count=len(preview_books),quality_queue_counts=dict(queue_counts),
                       english_books_without_passages=[sbook for sbook in sorted({s.book for s in sources if s.language=='English'}-preview_books)],
                       counts=dict(counters),extraction_failures=failures,encoding_recoveries=encoding_warnings,
                       teaching_scopes=[{'grade':g,'subject':s,'prose_candidates':c} for (g,s),c in sorted(scope_counts.items())],
                       extracted_complete=not failures,
                       elapsed_seconds=round(time.monotonic()-started,2))
        idx.execute('INSERT INTO metadata VALUES (?,?)',('build_receipt',json.dumps(receipt)))
        raw.commit(); idx.commit()
        raw.close(); idx.close()
        os.replace(rawpath,output/'staff_pages.sqlite')
        os.replace(indexpath,output/'preview.sqlite')
        receipt['outputs'] = {name:sha256(output/name) for name in ('staff_pages.sqlite','preview.sqlite')}
        (output/'BUILD_REPORT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding='utf-8')
    finally:
        raw.close(); idx.close()
    return receipt
