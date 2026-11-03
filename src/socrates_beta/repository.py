from __future__ import annotations
import hashlib,json,sqlite3,time,uuid
from contextlib import contextmanager
from pathlib import Path
from filelock import FileLock,Timeout


class BetaBusy(Exception):
    """The browser profile is processing another request."""


class Repository:
    def __init__(self,path: Path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,preferences TEXT,created REAL);
            CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,owner TEXT,dataset TEXT,scope TEXT,
              title TEXT,state TEXT,created REAL,updated REAL);
            CREATE INDEX IF NOT EXISTS owner_sessions ON sessions(owner,updated);
            CREATE TABLE IF NOT EXISTS turns(id INTEGER PRIMARY KEY,session_id TEXT,request_id TEXT,
              user_text TEXT,result TEXT,created REAL,UNIQUE(session_id,request_id));
            CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY,session_id TEXT,owner TEXT,mode TEXT,
              state TEXT,created REAL,updated REAL);
            CREATE TABLE IF NOT EXISTS observations(id INTEGER PRIMARY KEY,owner TEXT,session_id TEXT,node TEXT,
              kind TEXT,value TEXT,created REAL);
            CREATE TABLE IF NOT EXISTS cards(id TEXT PRIMARY KEY,owner TEXT,dataset TEXT,passage_id TEXT,
              front TEXT,back TEXT,source TEXT,bucket INTEGER,due REAL,created REAL,
              UNIQUE(owner,dataset,passage_id));
            CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY,owner TEXT,card_id TEXT,rating TEXT,created REAL);
            PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path,timeout=20);c.row_factory=sqlite3.Row
        c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA foreign_keys=ON')
        try:
            with c: yield c
        finally:c.close()

    @contextmanager
    def owner_guard(self, owner, *, timeout=30):
        # Fixed lock stripes avoid persistent per-profile filenames. Other
        # profiles can occasionally share a stripe; no model data enters it.
        stripe=hashlib.sha256(owner.encode('utf-8')).hexdigest()[:2]
        directory=Path(str(self.path.resolve())+'.profile-locks')
        directory.mkdir(parents=True,exist_ok=True)
        try:
            with FileLock(str(directory/(stripe+'.lock')),timeout=timeout,
                          preserve_lock_file=True,fallback_to_soft=False):
                yield
        except Timeout as exc:
            raise BetaBusy('Another request is still running. Please try again.') from exc

    @contextmanager
    def transaction(self):
        """Serialize assessment state transitions and commit their observations together."""
        with self.connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            yield conn

    @contextmanager
    def _using(self, conn):
        if conn is not None:
            yield conn
        else:
            with self.connect() as own:
                yield own

    @staticmethod
    def decode(row):
        if row is None:return None
        d=dict(row)
        for k in ('preferences','scope','state','result','source','value'):
            if k in d:d[k]=json.loads(d[k])
        return d

    def profile(self,owner):
        with self.connect() as c:
            row=c.execute('SELECT * FROM profiles WHERE id=?',(owner,)).fetchone()
            if row is None:
                c.execute('INSERT OR IGNORE INTO profiles VALUES (?,?,?)',(owner,'{}',time.time()))
                row=c.execute('SELECT * FROM profiles WHERE id=?',(owner,)).fetchone()
            return self.decode(row)

    def preferences(self,owner,prefs):
        self.profile(owner)
        with self.connect() as c:c.execute('UPDATE profiles SET preferences=? WHERE id=?',(json.dumps(prefs),owner))

    def session(self,sid,owner,*,conn=None):
        with self._using(conn) as c:r=c.execute('SELECT * FROM sessions WHERE id=? AND owner=?',(sid,owner)).fetchone()
        if r is None:raise KeyError('Session not found')
        return self.decode(r)

    def create_session(self,owner,dataset,scope,title):
        sid=uuid.uuid4().hex;now=time.time()
        state={'focus':'','stuck':0,'active_problem':False,'last_passages':[]}
        with self.connect() as c:c.execute('INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)',
          (sid,owner,dataset,json.dumps(scope),title[:120],json.dumps(state),now,now))
        return self.session(sid,owner)

    def sessions(self,owner):
        with self.connect() as c:return [self.decode(r) for r in c.execute('SELECT * FROM sessions WHERE owner=? ORDER BY updated DESC LIMIT 100',(owner,))]

    def history(self,sid):
        with self.connect() as c:return [self.decode(r) for r in c.execute('SELECT * FROM turns WHERE session_id=? ORDER BY id',(sid,))]

    def prior_turn(self,sid,key):
        with self.connect() as c:r=c.execute('SELECT result FROM turns WHERE session_id=? AND request_id=?',(sid,key)).fetchone()
        return json.loads(r[0]) if r else None

    def save_turn(self,sid,key,text,result,state):
        now=time.time()
        with self.connect() as c:
            c.execute('INSERT INTO turns(session_id,request_id,user_text,result,created) VALUES (?,?,?,?,?)',
              (sid,key,text,json.dumps(result),now))
            c.execute('UPDATE sessions SET state=?,updated=? WHERE id=?',(json.dumps(state),now,sid))

    def observe(self,owner,sid,node,kind,value,*,conn=None):
        with self._using(conn) as c:c.execute('INSERT INTO observations(owner,session_id,node,kind,value,created) VALUES (?,?,?,?,?,?)',
          (owner,sid,node,kind,json.dumps(value),time.time()))

    def observations(self,owner):
        with self.connect() as c:return [self.decode(r) for r in c.execute('SELECT * FROM observations WHERE owner=? ORDER BY id',(owner,))]

    def assessment(self,aid,owner,*,conn=None):
        with self._using(conn) as c:r=c.execute('SELECT * FROM assessments WHERE id=? AND owner=?',(aid,owner)).fetchone()
        if r is None:raise KeyError('Assessment not found')
        return self.decode(r)

    def assessments(self,owner):
        with self.connect() as c:
            rows=c.execute('SELECT * FROM assessments WHERE owner=? ORDER BY created,id',(owner,)).fetchall()
        return [self.decode(row) for row in rows]

    def active_assessment(self,sid,owner,*,conn=None):
        with self._using(conn) as c:rows=c.execute('SELECT * FROM assessments WHERE session_id=? AND owner=? ORDER BY created DESC',(sid,owner)).fetchall()
        return next((self.decode(r) for r in rows if not json.loads(r['state']).get('complete')),None)

    def open_check(self,owner,*,conn=None):
        with self._using(conn) as c:rows=c.execute("SELECT * FROM assessments WHERE owner=? AND mode IN ('quiz','diagnostic') ORDER BY created DESC",(owner,)).fetchall()
        return next((self.decode(r) for r in rows if not json.loads(r['state']).get('complete')),None)

    def save_assessment(self,record,*,conn=None):
        with self._using(conn) as c:c.execute('INSERT INTO assessments VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state,updated=excluded.updated',
            (record['id'],record['session_id'],record['owner'],record['mode'],json.dumps(record['state']),record['created'],time.time()))

    def cards(self,owner):
        with self.connect() as c:return [self.decode(r) for r in c.execute('SELECT * FROM cards WHERE owner=? ORDER BY due',(owner,))]

    def add_card(self,owner,dataset,p):
        now=time.time();cid=uuid.uuid4().hex
        front='Recall the key idea: '+p['title']
        # An extractive reference, not a generated answer or assessment key.
        back=p['text'][:1800]
        source={k:p[k] for k in ('id','title','page','source_id','source_sha256','source_url','human_review_status')}
        with self.connect() as c:c.execute('INSERT OR IGNORE INTO cards VALUES (?,?,?,?,?,?,?,?,?,?)',
          (cid,owner,dataset,p['id'],front,back,json.dumps(source),0,now,now))
        return next(x for x in self.cards(owner) if x['dataset']==dataset and x['passage_id']==p['id'])

    def review_card(self,owner,cid,rating):
        if rating not in ('again','hard','good','easy'):raise ValueError('Unknown rating')
        card=next((x for x in self.cards(owner) if x['id']==cid),None)
        if card is None:raise KeyError('Card not found')
        bucket=0 if rating=='again' else max(0,card['bucket']-1) if rating=='hard' else min(3,card['bucket']+(2 if rating=='easy' else 1))
        delay=[10*60,86400,3*86400,7*86400][bucket]
        with self.connect() as c:
            c.execute('UPDATE cards SET bucket=?,due=? WHERE id=? AND owner=?',(bucket,time.time()+delay,cid,owner))
            c.execute('INSERT INTO reviews(owner,card_id,rating,created) VALUES (?,?,?,?)',(owner,cid,rating,time.time()))
        return next(x for x in self.cards(owner) if x['id']==cid)

    def forget(self,owner):
        with self.connect() as c:
            c.execute('DELETE FROM turns WHERE session_id IN (SELECT id FROM sessions WHERE owner=?)',(owner,))
            for table in ('sessions','assessments','observations','cards','reviews'):
                c.execute(f'DELETE FROM {table} WHERE owner=?',(owner,))
            c.execute('DELETE FROM profiles WHERE id=?',(owner,))
