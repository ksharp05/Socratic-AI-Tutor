"""The only NCERT PDFs that may be indexed.

Decision D-4: the answers appendix (jemh1an) is never indexed, because the tutor could then retrieve
answers. Any chapter other than 4, 5 and 8 is out of scope (TP-T5) and is refused as well.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

ANSWERS_APPENDIX = "jemh1an"


@dataclass(frozen=True)
class Source:
    stem: str
    source_id: str
    chapter: str
    chapter_number: int
    sha256: str  # hash recorded in the dataset's card anchors (content/dataset-v0.10.0/corpus.jsonl)

    @property
    def url(self) -> str:
        return f"https://ncert.nic.in/textbook/pdf/{self.stem}.pdf"


ALLOWED: dict[str, Source] = {s.stem: s for s in (
    Source("jemh104", "ncert_qe", "quadratic_equations", 4,
           "9aca4b28ad57ae78a5e69ce67d19344c44b1390c5b8afd13db83b46ad54e8e9d"),
    Source("jemh105", "ncert_ap", "arithmetic_progressions", 5,
           "1367857e5cd3206b1862655d17bf31778e6af768821d8dfc8c71d3ea0e19274c"),
    Source("jemh108", "ncert_trig", "trigonometry", 8,
           "5a4033fd2ab3fbb245f783a3e2c24fb5c31a00ae7fa7b9a7212633d11e06d2ac"),
)}


class RefusedSource(ValueError):
    """Raised for the answers appendix and for any chapter outside 4, 5 and 8."""


def resolve(name: str | Path) -> Source:
    """Returns the allowed source for a stem or PDF path, or raises RefusedSource."""
    stem = Path(str(name)).stem.lower()
    if stem.startswith(ANSWERS_APPENDIX):
        raise RefusedSource(f"REFUSED: {stem} is the answers appendix; indexing it would let the tutor "
                            "retrieve answers (decision D-4)")
    if stem not in ALLOWED:
        raise RefusedSource(f"REFUSED: {stem} is not chapter 4, 5 or 8 of Class 10 NCERT maths; only "
                            f"{', '.join(sorted(ALLOWED))} may be indexed")
    return ALLOWED[stem]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
