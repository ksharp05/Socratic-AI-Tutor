"""Split extracted NCERT pages into section chunks with stable passage IDs.

Input is one string per PDF page (as `pdftotext -layout` prints them). Rules, from
Docs/plan/04-architecture.md "Chunking":
- split on the chapter's section headings (4.1, 4.2, ...), which must appear in order;
- inside a section, start a new chunk at each "Example n" (kept with its solution) and each "EXERCISE";
- cap chunks at about MAX_WORDS words, splitting only after a paragraph that ends a sentence, so a
  display equation (whose numerator and denominator sit on separate lines) is never cut;
- passage IDs are deterministic: ncert:<stem>:s<section>:c<NN>, numbered from 01 within each section.

Deviation from the plan, for now: an exercise is kept as one block (capped) rather than one chunk per
question.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .textnorm import repair_symbols

MAX_WORDS = 350
_FOOTER = re.compile(r"^\s*Reprint\s+\d{4}-\d{2}\s*$")
_EXAMPLE = re.compile(r"^\s*Example\s+\d+\s*:")
_EXERCISE = re.compile(r"^\s*EXERCISE\s+\d+\.\d+\s*$")


@dataclass
class Chunk:
    passage_id: str
    source_stem: str
    chapter: str
    chapter_number: int
    section: str
    section_title: str
    kind: str  # theory | example | exercise
    pdf_page: int
    printed_page: int | None
    pdf_pages: list[int] = field(default_factory=list)
    printed_pages: list[int] = field(default_factory=list)
    text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def printed_page_of(page_text: str) -> int | None:
    """NCERT running heads put the printed page number at the start or end of the first line."""
    for line in page_text.splitlines():
        if line.strip():
            m = re.match(r"^\s*(\d{1,3})\s+\S", line) or re.search(r"\S\s+(\d{1,3})\s*$", line)
            return int(m.group(1)) if m else None
    return None


def _body_lines(page_text: str) -> list[str]:
    """Drops the running head (first non-blank line) and the reprint footer."""
    lines, seen_head = [], False
    for line in page_text.splitlines():
        if not seen_head and line.strip():
            seen_head = True
            if printed_page_of(line) is not None:
                continue
        if _FOOTER.match(line):
            continue
        lines.append(line)
    return lines


def _heading(line: str, chapter_number: int, expected: int) -> str | None:
    m = re.match(rf"^\s{{0,8}}{chapter_number}\.(\d+)\s+([A-Za-z].*?)\s*(?:\s{{3,}}.*)?$", line)
    if m and int(m.group(1)) == expected:
        return m.group(2).strip()
    return None


def _clean(lines: list[str]) -> str:
    text = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _split_capped(lines: list[tuple[str, int, int | None]]) -> list[list[tuple[str, int, int | None]]]:
    """Splits a block at sentence-ending paragraph breaks once it passes MAX_WORDS."""
    parts, current, words = [], [], 0
    for i, item in enumerate(lines):
        current.append(item)
        words += len(item[0].split())
        blank_next = i + 1 < len(lines) and not lines[i + 1][0].strip()
        sentence_end = item[0].rstrip().endswith((".", "?", ":"))
        # Past twice the cap, any break before a prose line will do (no sentence end was found).
        prose_next = i + 2 < len(lines) and re.match(r"^\s*[A-Za-z]{3,}", lines[i + 2][0]) is not None
        if blank_next and ((words >= MAX_WORDS and sentence_end) or (words >= 2 * MAX_WORDS and prose_next)):
            parts.append(current)
            current, words = [], 0
    if any(line.strip() for line, _, _ in current):
        parts.append(current)
    return parts


def _take_fraction_tail(block: list) -> list:
    """Layout mode prints a fraction's numerator on the line above its text, so a numerator can sit
    just before an "Example n" line. Moves such short fragments (and blank lines) to the new block."""
    tail = []
    while block and (not block[-1][0].strip() or len(block[-1][0].strip()) <= 12
                     and not block[-1][0].rstrip().endswith((".", ":"))):
        tail.insert(0, block.pop())
    return [item for item in tail if item[0].strip()]


def chunk_pages(pages: list[str], *, stem: str, chapter: str, chapter_number: int) -> list[Chunk]:
    """Chunks one chapter. `pages[i]` is the text of PDF page i + 1."""
    tagged: list[tuple[str, int, int | None]] = []
    for index, page in enumerate(pages):
        page = repair_symbols(page)
        printed = printed_page_of(page)
        tagged.extend((line, index + 1, printed) for line in _body_lines(page))

    # Sections: anything before the first heading (chapter title, opening text) joins section n.1.
    sections: list[tuple[str, str, list]] = []
    expected, title, current = 1, None, []
    for item in tagged:
        found = _heading(item[0], chapter_number, expected)
        if found is not None:
            if title is not None:
                sections.append((f"{chapter_number}.{expected - 1}", title, current))
                current = []
            title, expected = found, expected + 1
            continue
        current.append(item)
    if title is None:
        raise ValueError(f"{stem}: no section headings for chapter {chapter_number} were found")
    sections.append((f"{chapter_number}.{expected - 1}", title, current))

    chunks: list[Chunk] = []
    for section, sec_title, lines in sections:
        blocks: list[tuple[str, list]] = [("theory", [])]
        for item in lines:
            kind = "example" if _EXAMPLE.match(item[0]) else "exercise" if _EXERCISE.match(item[0]) else None
            if kind:
                blocks.append((kind, _take_fraction_tail(blocks[-1][1])))
            blocks[-1][1].append(item)
        n = 0
        for kind, block in blocks:
            for part in _split_capped(block):
                text = _clean([line for line, _, _ in part])
                if not text:
                    continue
                n += 1
                content = [(p, q) for line, p, q in part if line.strip()]
                pdf_pages = sorted({p for p, _ in content})
                printed = sorted({q for _, q in content if q is not None})
                chunks.append(Chunk(
                    passage_id=f"ncert:{stem}:s{section}:c{n:02d}", source_stem=stem, chapter=chapter,
                    chapter_number=chapter_number, section=section, section_title=sec_title, kind=kind,
                    pdf_page=pdf_pages[0], printed_page=printed[0] if printed else None,
                    pdf_pages=pdf_pages, printed_pages=printed, text=text))
    return chunks
