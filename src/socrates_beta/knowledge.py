from __future__ import annotations
import difflib,hashlib,json,os,re,shutil,sqlite3,subprocess,threading,time
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
from ncert_pipeline.build import SCHEMA,insert_passage
from ncert_pipeline.catalogue import sha256,read_json
from ncert_pipeline.retrieval import query_terms
from .ports import Scope

EXTRA_STOP=set('on know understand get need explain simple english mean means difference between like example please still confused tell help think happens happen work works make makes use used can want would us them they their'.split())
ALIASES={'photosyntesis':'photosynthesis','photosyntheis':'photosynthesis','co2':'carbon dioxide','a.p.':'arithmetic progression',
         'ap':'arithmetic progression','q.e.':'quadratic','trig':'trigonometry','dna copying':'dna replication'}
TRIG_SPELLINGS={'sine':'sin','cosine':'cos','tangent':'tan'}
# Filler words in English and Hinglish that must not drive retrieval on their own ("at", "never", "kya", "batao").
EXTRA_STOP|=set("""a an the is are was were be been being am do does did done doing how why what when where which who whom whose
i me my mine you your yours he she it its we our this that these those there here of in at to from by for with about as into onto over
under up down out off and or but if then so than too very just also only even again ever never not no yes could should will shall may
might must have has had having got gets getting made wants needs knows tell thanks thank sir maam bro yaar bhai bhaiya lol omg ok okay
fine anyway really say said easy easily words word hindi way thing things something anything someone people everyone class today
tomorrow test exam exams boards board marks teacher friend friends mom dad parents feel feeling stressed hard tough hate love ka ki ke
ko kya hai hain hota hoti hote hun hoon tha thi mein me se aur par pe toh bhi nahi na kaise kyun kab kitna kitni batao bata samjha
samjhao samajh aa raha rahi de dena karo kar karna karte nikalne nikale nikalte wala wali wale ye yeh vo woh bohot bahut thoda jaldi
mujhe hume humein apna apni""".split())
# NCERT Hindi and common Hinglish maths terms, mapped to the English words the index uses.
GLOSSARY={'द्विघात':'quadratic','समीकरण':'equation','विविक्तकर':'discriminant','मूलों':'roots','मूल':'root','समांतर':'arithmetic',
          'श्रेढ़ी':'progression','श्रेढी':'progression','सार्व':'common','अंतर':'difference','पद':'term','योग':'sum',
          'त्रिकोणमितीय':'trigonometric','त्रिकोणमिति':'trigonometry','अनुपात':'ratio','कर्ण':'hypotenuse','कोण':'angle',
          'मानक':'standard','सूत्र':'formula','मान':'value','samantar':'arithmetic','shredhi':'progression','mool':'root','yog':'sum',
          'antar':'difference','sutra':'formula','discrmnt':'discriminant'}
# Words too common in the textbook to show that a passage is about the question.
GENERIC=set('first same each one two three term number numbers side value values use check keep zero least given find value'.split())
# Words specific enough that one of them shows what the question is about, however chatty the rest is.
STRONG=set('sin cos tan sine cosine tangent sec cosec cot trigonometry trigonometric hypotenuse discriminant quadratic progression arithmetic nth'.split())


def fold(word):
    """Singular form for matching: roots -> root, progressions -> progression."""
    if len(word)>4 and word.endswith('ies'):return word[:-3]+'y'
    if len(word)>4 and word.endswith('es') and word[-3] in 'sxz':return word[:-2]
    if len(word)>3 and word.endswith('s') and not word.endswith('ss'):return word[:-1]
    return word
@lru_cache(maxsize=1024)
def _source_words(text: str) -> frozenset[str]:
    words = set(re.findall('[a-z0-9]+',text.casefold()))
    return frozenset(words | {fold(word) for word in words})


@lru_cache(maxsize=1024)
def _passage_words(text: str, title: str, note: str) -> frozenset[str]:
    expanded = (text+' '+title+' '+note).casefold()
    for acronym,meaning in ALIASES.items():
        expanded += ' '+re.sub(r'(?<!\w)'+re.escape(acronym)+r'(?!\w)',meaning,text.casefold())
    for spelled,short in TRIG_SPELLINGS.items():
        if re.search(r'(?<!\w)(?:'+re.escape(spelled)+'|'+re.escape(short)+r')(?!\w)',expanded):
            expanded += ' '+spelled+' '+short
    return _source_words(expanded)


SAFE_ID=re.compile(r'^[a-z0-9][a-z0-9_-]{2,79}$')


@contextmanager
def database(*args,**kwargs):
    connection=sqlite3.connect(*args,**kwargs)
    try:
        with connection:yield connection
    finally:connection.close()


class DatasetRegistry:
    def __init__(self,root: Path):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'registry.json';self.lock=threading.RLock();self.cache={}
        if not self.path.exists():self._write({'schema':1,'active':None,'datasets':{}})
    def _write(self,data):
        temp=self.path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(temp,self.path)
    def entries(self):return read_json(self.path)
    def register(self,dataset_id,index: Path,*,title,activate=False,provenance=None,expected_sha256=None):
        if not SAFE_ID.fullmatch(dataset_id):raise ValueError('Use a dataset id with lowercase letters, numbers and hyphens')
        index=Path(index).resolve(strict=True)
        with database(index.as_uri()+'?mode=ro',uri=True) as c:
            if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Index integrity failure')
            required={'id','source_id','book','subject','title','page','text','source_sha256','source_url','kind','human_review_status'}
            if not required <= {r[1] for r in c.execute('PRAGMA table_info(passages)')}:raise ValueError('Incompatible knowledge index')
            n=c.execute('SELECT count(*) FROM passages').fetchone()[0]
            if n<1:raise ValueError('Empty dataset')
            if c.execute('SELECT count(*) FROM scopes WHERE grade NOT BETWEEN 8 AND 12').fetchone()[0]:raise ValueError('Unsupported grade')
            # The index must have a functioning text search and anchored, review-labelled passages.
            c.execute('SELECT count(*) FROM search').fetchone()
            for pid,page,h,status in c.execute('SELECT id,page,source_sha256,human_review_status FROM passages'):
                if not pid or not isinstance(page,int) or page<1 or not re.fullmatch('[0-9a-f]{64}',h) or status!='pending':
                    raise ValueError('Unanchored or unreviewed-status-misrepresented passage')
        digest=sha256(index)
        if expected_sha256 is not None:
            if not re.fullmatch(r'[0-9a-f]{64}',expected_sha256):raise ValueError('Expected SHA-256 must be 64 lowercase hexadecimal characters')
            if digest!=expected_sha256:raise ValueError('Index SHA-256 does not match the expected value')
        with self.lock:
            data=self.entries();previous=data['datasets'].get(dataset_id)
            if previous and previous['sha256']!=digest:raise ValueError('Dataset versions are immutable; choose a new id')
            data['datasets'][dataset_id]={'id':dataset_id,'path':str(index),'sha256':digest,'title':str(title)[:160],
                'passages':n,'registered':time.time(),'review_status':'pending','provenance':provenance or {}}
            if activate or not data['active']:data['active']=dataset_id
            self._write(data)
        return data['datasets'][dataset_id]
    def activate(self,dataset_id):
        self.knowledge(dataset_id)
        with self.lock:
            data=self.entries();data['active']=dataset_id;self._write(data)
    def knowledge(self,dataset_id=None):
        data=self.entries();dataset_id=dataset_id or data['active'];entry=data['datasets'].get(dataset_id)
        if entry is None:raise KeyError('Dataset not registered')
        path=Path(entry['path']);stat=path.stat();stamp=(stat.st_size,stat.st_mtime_ns)
        with self.lock:
            cached=self.cache.get(dataset_id)
            if cached and cached[0]==stamp:return cached[1]
            if sha256(path)!=entry['sha256']:raise ValueError('Dataset changed after registration; refusing stale evidence')
            adapter=SqliteKnowledge(dataset_id,path)
            self.cache[dataset_id]=(stamp,adapter)
            return adapter
    def public(self):
        data=self.entries()
        return {'active':data['active'],'datasets':[{k:v[k] for k in ('id','title','passages','review_status','sha256')} for v in data['datasets'].values()]}


class SqliteKnowledge:
    def __init__(self,dataset_id,path):
        self.dataset_id,self.path=dataset_id,Path(path)
        with self.connect() as c:
            # Vocabulary is used only for conservative spelling repair, not generation.
            try:
                c.execute('CREATE VIRTUAL TABLE temp.lexicon USING fts5vocab(main, search, row)')
                self.vocabulary={r[0] for r in c.execute('SELECT term FROM temp.lexicon WHERE length(term)>4')}
            except sqlite3.Error:self.vocabulary=set()
        self.prefixes={}
        for word in self.vocabulary:self.prefixes.setdefault(word[:3],[]).append(word)
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
        try:yield c
        finally:c.close()
    def catalogue(self):
        with self.connect() as c:
            return [dict(r) for r in c.execute('''SELECT s.grade,p.subject,p.book,min(p.title) title,count(*) passages
              FROM scopes s JOIN passages p ON p.id=s.passage_id GROUP BY s.grade,p.subject,p.book ORDER BY s.grade,p.subject,p.book''')]
    def terms(self,query):
        q=query.casefold()
        for a,b in GLOSSARY.items():q=q.replace(a,' '+b+' ')
        for a,b in ALIASES.items():q=re.sub(r'(?<!\w)'+re.escape(a)+r'(?!\w)',b,q)
        terms=[t for t in query_terms(q) if t not in EXTRA_STOP]
        terms=[v for t in terms for v in dict.fromkeys((t,fold(t)))]
        # Keep the learner's English spelling and add mathematical abbreviations.
        terms=[variant for term in terms for variant in ((term, TRIG_SPELLINGS[term]) if term in TRIG_SPELLINGS else (term,))]
        if 'arithmetic progression' in q:terms.append('ap')
        fixed=[]
        for t in terms:
            if len(t)>=7 and t not in self.vocabulary:
                matches=difflib.get_close_matches(t,self.prefixes.get(t[:3],[]),n=1,cutoff=.9)
                t=matches[0] if matches and matches[0][:3]==t[:3] else t
            fixed.append(t)
        return list(dict.fromkeys(fixed))[:16]
    def search(self,query,scope: Scope,limit=3):
        if type(scope.grade) is not int or not 8<=scope.grade<=12:raise ValueError('Unsupported grade')
        from .topics import broad_topic
        opening=broad_topic(self,query,scope)
        if opening:
            # Resolve broad chapter names via admitted concepts even when the
            # literal chapter title is absent from the reference passage text.
            ids=list(dict.fromkeys(pid for node in opening for pid in node.get('passage_ids',[])))
            passages=[self.passage(pid) for pid in ids]
            return [p for p in passages if p is not None][:max(1,min(limit,6))]
        terms=self.terms(query)
        if not terms:return []
        args=[' OR '.join('"'+t+'"' for t in terms),scope.grade,scope.subject.casefold()]
        sql='''SELECT p.*,bm25(search,0,1,1.3) rank FROM search JOIN passages p ON p.id=search.passage_id
          JOIN scopes s ON s.passage_id=p.id WHERE search MATCH ? AND s.grade=? AND s.subject=?'''
        if scope.book:sql+=' AND p.book=?';args.append(scope.book)
        if scope.unit is not None:sql+=' AND p.unit_file_index=?';args.append(scope.unit)
        sql+=' ORDER BY rank,p.id LIMIT 40'
        with self.connect() as c:rows=[dict(r) for r in c.execute(sql,args)]
        # Reference notes replace terse passages after ranking; their words count too, and a passage whose note alone
        # matches is still a candidate (e.g. the nth-term note for "nth term" questions).
        extra=getattr(self,'extra_text',{})
        seen={p['id'] for p in rows};floor_rank=max([p['rank'] for p in rows],default=-1.0)
        for pid,text in extra.items():
            if pid in seen:continue
            words=_source_words(text)
            if sum(t in words for t in terms)<max(1,len(terms)/2) or not any(t in words and t not in GENERIC for t in terms):continue
            p=self.passage(pid)
            if p and self._in_scope(pid,scope):rows.append({**p,'rank':floor_rank})
        for p in rows:
            words=_passage_words(p['text'],p['title'],extra.get(p['id'],''))
            hits=[t for t in terms if t in words]
            p['query_coverage']=len(hits)/len(terms)
            p['domain_hits']=sum(t not in GENERIC for t in hits)
            p['strong_hits']=sum(t in STRONG for t in hits)
            p['_hits']=hits
        # Rare query words say more about the question than words every candidate shares ("nth" vs "term").
        df={t:sum(t in p['_hits'] for p in rows) for t in terms}
        weight={t:1/df[t] for t in terms if df[t]}
        for p in rows:
            share=sum(weight.get(t,0) for t in p.pop('_hits'))/(sum(weight.values()) or 1)
            p['retrieval_score']=round(-p['rank']*(.5+share),4)
        # Relevance floor: a passage must share a subject word with the question, and enough of the question,
        # so that filler like "at" or "zero" no longer links unrelated questions to a passage.
        rows=[p for p in rows if p['domain_hits']>=1 and (p['query_coverage']>=.2 or p['domain_hits']>=2 or p['strong_hits'])]
        rows.sort(key=lambda p:(-p['retrieval_score'],p['id']))
        if re.search(r'(?i)\b(?:what is|what are|what makes|define)\b',query) and rows:
            with self.connect() as c:
                prerequisites={r[0]:len(json.loads(r[1])) for r in c.execute('SELECT id,prerequisites FROM concepts')} if c.execute("SELECT 1 FROM sqlite_master WHERE name='concepts'").fetchone() else {}
            best_coverage=max(p['query_coverage'] for p in rows)
            def foundational(p):
                cid=p['id'].removeprefix('normalized:')
                return cid in prerequisites and prerequisites[cid]==0 and p['query_coverage']>=best_coverage-.15
            rows.sort(key=lambda p:(not foundational(p),-p['retrieval_score'],p['id']))
        return rows[:max(1,min(limit,6))]
    def passage(self,pid):
        with self.connect() as c:r=c.execute('SELECT * FROM passages WHERE id=?',(pid,)).fetchone()
        return dict(r) if r else None
    def _in_scope(self,pid,scope):
        sql='SELECT 1 FROM scopes s JOIN passages p ON p.id=s.passage_id WHERE p.id=? AND s.grade=? AND s.subject=?'
        args=[pid,scope.grade,scope.subject.casefold()]
        if scope.book:sql+=' AND p.book=?';args.append(scope.book)
        if scope.unit is not None:sql+=' AND p.unit_file_index=?';args.append(scope.unit)
        with self.connect() as c:return c.execute(sql,args).fetchone() is not None
    def nodes(self,scope):
        if scope.grade==10 and scope.subject.casefold()=='mathematics' and (not scope.book or scope.book=='jemh1'):
            with self.connect() as c:
                if c.execute("SELECT 1 FROM sqlite_master WHERE name='concepts'").fetchone():
                    result=[]
                    for row in c.execute('SELECT * FROM concepts ORDER BY unit,id'):
                        d=dict(row)
                        if scope.unit is not None and d['unit']!=scope.unit:continue
                        d.update(kind='concept',book='jemh1',unit_file_index=d.pop('unit'),passages=1,
                                 prerequisites=json.loads(d['prerequisites']),passage_ids=json.loads(d['passage_ids']))
                        result.append(d)
                    return result
        sql='''SELECT p.book,p.unit_file_index,min(p.page) page,count(*) passages,min(p.title) title
           FROM passages p JOIN scopes s ON s.passage_id=p.id WHERE s.grade=? AND s.subject=?'''
        args=[scope.grade,scope.subject.casefold()]
        if scope.book:sql+=' AND p.book=?';args.append(scope.book)
        sql+=' GROUP BY p.book,p.unit_file_index ORDER BY p.book,p.unit_file_index'
        with self.connect() as c:rows=[dict(r) for r in c.execute(sql,args)]
        with self.connect() as c:
            titles={(x[0],x[1]):x[2] for x in c.execute('SELECT book,unit,title FROM readings')} if c.execute("SELECT 1 FROM sqlite_master WHERE name='readings'").fetchone() else {}
        for r in rows:
            r['id']=f"reading:{r['book']}:{r['unit_file_index']}"
            r['kind']='reading';r['prerequisites']=[]
            title=r['title'].split(' — ',1)[-1]
            r['title']=titles.get((r['book'],r['unit_file_index'])) or (title if ' — ' in r['title'] else (f"{title} · Reading {r['unit_file_index']}" if r['unit_file_index'] is not None else title))
        return rows


def normalize_quote(text):return re.sub(r'\s+',' ',text).strip()


def import_jsonl(source: Path,index: Path,*,tool: Path=Path('C:/Program Files/Git/mingw64/bin/pdftotext.exe')):
    """Operator-only adapter: exact source quotes, verified original hashes, no runtime upload."""
    index=Path(index)
    if index.exists():raise ValueError('Refusing to replace an index')
    rows=[];page_cache={}
    for line in Path(source).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        r=json.loads(line)
        needed={'id','grades','subject','book','title','text','page','source_file','source_sha256','source_url'}
        if not needed<=set(r):raise ValueError('Incomplete passage record')
        if not re.fullmatch(r'[A-Za-z0-9:_-]{3,100}',r['id']):raise ValueError('Invalid passage id')
        if r['subject'].casefold()=='mathematics':raise ValueError('Maths requires a normalized-reference/checker adapter, not raw quote import')
        if not r['grades'] or any(type(g) is not int or not 8<=g<=12 for g in r['grades']):raise ValueError('Unsupported grade')
        if type(r['page']) is not int or r['page']<1 or not 35<=len(r['text'])<=2200:raise ValueError('Invalid page/text bounds')
        original=Path(r['source_file']).resolve(strict=True)
        if sha256(original)!=r['source_sha256']:raise ValueError('Original source hash mismatch')
        if urlparse(r['source_url']).scheme not in ('http','https'):raise ValueError('Use an HTTP(S) source citation')
        key=(str(original),r['page'])
        if key not in page_cache:
            if original.suffix.lower()=='.txt':
                if r['page']!=1:raise ValueError('Text-source pages must be 1')
                page_cache[key]=original.read_text(encoding='utf-8-sig')
            elif original.suffix.lower()=='.pdf':
                proc=subprocess.run([str(tool),'-f',str(r['page']),'-l',str(r['page']),'-layout','-enc','UTF-8',str(original),'-'],capture_output=True,timeout=30,check=True)
                page_cache[key]=proc.stdout.decode('utf-8',errors='strict')
            else:raise ValueError('Adapter accepts text or PDF originals')
        if normalize_quote(r['text']) not in normalize_quote(page_cache[key]):raise ValueError('Passage is not an exact source-page quote')
        r.update(source_id=r.get('source_id') or original.name,unit_file_index=r.get('unit_file_index'),kind='source_prose',human_review_status='pending')
        rows.append(r)
    if not rows:raise ValueError('Empty import')
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate passage id')
    index.parent.mkdir(parents=True,exist_ok=True)
    staging=index.with_suffix('.building.sqlite')
    if staging.exists():raise ValueError('An unfinished import exists; inspect it before retrying')
    try:
        with database(staging) as c:
            c.executescript(SCHEMA)
            for r in rows:insert_passage(c,r,r['grades'])
            c.execute('INSERT INTO metadata VALUES (?,?)',('import',json.dumps({'adapter':'passage-jsonl-v1','source_sha256':sha256(source),'count':len(rows),'review_status':'pending'})))
        os.replace(staging,index)
    except Exception:
        if staging.exists():staging.unlink()
        raise
    return len(rows)
