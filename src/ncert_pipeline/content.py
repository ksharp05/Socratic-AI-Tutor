from __future__ import annotations
import re
from collections import Counter

# These rules reduce exposure in a development preview; semantic review is still pending.
STOP = re.compile(r'^\s*(?:examples?\b|solutions?\b|exercises?\b|answers?\b|questions?\b|'
                  r'what\s+you\s+have\s+learnt|summary\b|review\s+questions?\b|'
                  r'activities\b|activity\b|in.text\s+questions?\b|let.s\s+(?:assess|recall|explore|do|discuss))', re.I)
SECTION = re.compile(r'^\s*\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\s+[A-Za-z][A-Za-z ,:()\-]{3,100}$')
FOOT = re.compile(r'^(?:reprint\b|rationalised\b|\d{1,3}\s*$|chapter\s*\d+\s*$|\d{4}.\d{2}\s*$)', re.I)


def clean(text: str) -> str:
    # Keep raw pages separately. This cleans whitespace only, never repairs equations.
    return re.sub(r'\s+', ' ', text).strip()


def page_quality(text: str) -> str:
    if len(re.findall(r'\w', text, re.U)) < 25:
        return 'needs_ocr_or_sparse'
    letters = [c for c in text if c.isalpha()]
    bad = sum(c == '\ufffd' or '\ue000' <= c <= '\uf8ff' for c in text)
    if '\ufffd' in text or bad / max(1, len(text)) > .015:
        return 'glyph_damage'
    ascii_letters = sum(c.isascii() for c in letters)
    if ascii_letters / max(1, len(letters)) < .85:
        return 'non_english_or_glyphs'
    return 'candidate_english_text'


def concept_chunks(pages: list[str], *, subject: str, language: str,
                   numbered_asset: bool):
    """Cross-page exclusion state. Maths raw text cannot enter the formula lane."""
    stats = Counter()
    blocked, terminal, heading = False, False, ''
    for page_no, raw in enumerate(pages, 1):
        quality = page_quality(raw)
        stats[quality] += 1
        eligible_page = (quality == 'candidate_english_text' and language == 'English'
                         and subject != 'Mathematics' and numbered_asset)
        blocks, buf = [], []
        def flush():
            if buf:
                blocks.append(clean(' '.join(buf)))
                buf.clear()
        # Windows Poppler emits CR-CR-LF; splitlines alone inserts spurious blank paragraphs.
        layout = raw.replace('\r\r\n','\n').replace('\r\n','\n').replace('\r','\n')
        for line in layout.split('\n'):
            line = line.strip()
            if not line:
                flush()
                continue
            compact = re.sub(r'\s+','',line).upper()
            if re.match(r'^(?:EXERCISES?|ANSWERS?|REVIEWQUESTIONS?|APPENDIX)(?:$|[0-9:])',compact):
                flush(); blocked = True; terminal = True
                continue
            if STOP.match(line):
                flush(); blocked = True
                continue
            if not terminal and SECTION.fullmatch(line):
                flush(); blocked = False; heading = clean(line)
                continue
            if FOOT.match(line):
                continue
            if blocked:
                stats['lines_excluded_by_section'] += 1
                continue
            # Columns, symbolic lines, questions and task instructions stay out of this lane.
            words = line.split()
            symbols = sum(c in '=+*/<>^{}|\\' or '\ue000' <= c <= '\uf8ff' for c in line)
            if ('?' in line or re.search(r'\b(?:calculate|solve|find the|answer the|show that|prove that)\b', line, re.I)
                    or symbols > 1 or re.search(r'\S\s{4,}\S', line)):
                flush(); stats['lines_excluded_task_table_math'] += 1
                continue
            if len(words) < 3:
                flush()
                continue
            buf.append(line)
            if sum(len(x.split()) for x in buf) >= 130:
                flush()
        flush()
        if not eligible_page:
            stats['pages_outside_prose_preview'] += 1
            continue
        index = 0
        for block in blocks:
            # Short labels and diagram debris are not teaching passages.
            if re.search(r'\b(?:true or false|answer the|prove that|show that|choose the correct|fill in the blanks)\b|\([abcd]\).*\([abcd]\)',block,re.I):
                stats['task_blocks_excluded'] += 1
                continue
            if len(block.split()) < 35:
                stats['short_blocks_excluded'] += 1
                continue
            # Sentence-like material only; formula fidelity is never inferred from this.
            if not re.search(r'[.!;:]', block):
                continue
            # Bound input tokens even for a text dump with no paragraph boundaries.
            words = block.split()
            for start in range(0, len(words), 180):
                part = ' '.join(words[start:start+180])
                if len(part.split()) >= 35:
                    index += 1
                    yield {'page': page_no, 'ordinal': index, 'text': part,
                           'heading': heading, 'kind': 'extracted_prose_preview'}, stats
    # Caller supplies a mutable stats counter by reading the final yielded sentinel.
    yield None, stats
