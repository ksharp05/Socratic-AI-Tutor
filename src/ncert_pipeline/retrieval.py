from __future__ import annotations
import re, sqlite3
from contextlib import contextmanager
from pathlib import Path

STOPWORDS = set('a an the is are was were do does did how why what when where which who i me my you your can could would should please explain tell about of in to and or it this that for with have has from we us'.split())


def query_terms(query: str):
    return list(dict.fromkeys(t.casefold() for t in re.findall(r'[A-Za-z][A-Za-z0-9_]{1,35}',query)
                             if t.casefold() not in STOPWORDS))[:16]


class Retriever:
    def __init__(self, db: Path):
        self.path = Path(db).resolve(strict=True)

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True)
        conn.row_factory = sqlite3.Row
        try: yield conn
        finally: conn.close()

    def scopes(self):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute('SELECT grade,subject,COUNT(*) passages FROM scopes GROUP BY grade,subject ORDER BY grade,subject')]

    def search(self, query: str, *, grade: int, subject: str, book: str | None=None,
               unit_file_index: int | None=None, limit: int=4):
        if type(grade) is not int or not 8 <= grade <= 12 or not subject.strip():
            raise ValueError('A Class 8–12 and an explicit subject are required')
        terms = query_terms(query)
        if not terms: return []
        match = ' OR '.join('"'+t+'"' for t in terms)
        sql = '''SELECT p.*,bm25(search,0,1,1.5) rank FROM search
                 JOIN passages p ON p.id=search.passage_id
                 JOIN scopes s ON s.passage_id=p.id
                 WHERE search MATCH ? AND s.grade=? AND s.subject=?'''
        args = [match,grade,subject.casefold().strip()]
        if book is not None:
            sql += ' AND p.book=?'; args.append(book)
        if unit_file_index is not None:
            sql += ' AND p.unit_file_index=?'; args.append(unit_file_index)
        sql += ' ORDER BY rank,p.id LIMIT ?'; args.append(max(1,min(limit,8)))
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql,args)]
