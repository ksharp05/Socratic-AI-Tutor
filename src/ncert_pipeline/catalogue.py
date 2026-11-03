from __future__ import annotations
import hashlib, json, re
from dataclasses import asdict, dataclass
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


@dataclass(frozen=True)
class Source:
    source_id: str
    path: str
    sha256: str
    pages: int
    book: str
    grades: list[int]
    subject: str
    language: str
    title: str
    unit_file_index: int | None
    source_url: str

    def dict(self):
        return asdict(self)


def load_sources(manifest: Path, root: Path):
    """Follow only hash-bound manifests. Never glob private datasets/evaluations."""
    root = root.resolve(strict=True)
    allowed = [root / 'Directions' / 'ncert_all_subjects_8_12',
               root / 'Directions' / 'ncert_maths_8_12']

    def inside(path: Path):
        p = path.resolve(strict=True)
        if not any(p.is_relative_to(a.resolve()) for a in allowed):
            raise ValueError(f'Source path outside the textbook collections: {p.name}')
        return p

    manifest = inside(manifest)
    top = read_json(manifest)
    sources, excluded, seen = [], [], set()
    for entry in top['books']:
        vp = inside(Path(entry['volume_manifest']))
        if sha256(vp) != entry['manifest_sha256']:
            raise ValueError(f'Volume manifest hash mismatch: {entry["book_code"]}')
        v = read_json(vp)
        if v['book_code'] != entry['book_code']:
            raise ValueError('Book identity mismatch')
        grades = v['grades']
        if not grades or any(type(g) is not int or not 8 <= g <= 12 for g in grades):
            raise ValueError('Unsupported grade metadata')
        for o in v['originals']:
            sid = v['book_code'] + '/' + o['name']
            if sid in seen:
                raise ValueError(f'Duplicate source identity: {sid}')
            seen.add(sid)
            if o.get('pdf_parse') == 'failed' or not o.get('pages'):
                excluded.append({'source_id': sid, 'reason': 'publisher_pdf_defect'})
                continue
            p = inside(Path(o['absolute_path']))
            if p.suffix.lower() != '.pdf' or sha256(p) != o['sha256']:
                raise ValueError(f'PDF hash/extension mismatch: {sid}')
            match = re.fullmatch(re.escape(v['book_code']) + r'(\d{2})\.+pdf', o['name'], re.I)
            sources.append(Source(sid, str(p), o['sha256'], o['pages'], v['book_code'],
                grades, v['subject'], v['language_inferred_from_catalogue'],
                v['catalogue_title'], int(match[1]) if match else None,
                o.get('source_url') or o.get('source_url_candidate') or v.get('archive_url', '')))
    return sources, {'manifest_sha256': sha256(manifest), 'volume_count': len(top['books']),
                     'source_count': len(sources), 'expected_pages': sum(s.pages for s in sources),
                     'excluded_sources': excluded}
