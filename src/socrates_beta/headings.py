from __future__ import annotations
import re


def chapter_title(raw: str) -> str | None:
    # Heading metadata only. This mapping is not used to repair mathematical source text.
    raw=''.join(chr(ord(c)-0xf000) if 0xf020<=ord(c)<=0xf07e else c for c in raw)
    lines=[x.strip() for x in raw.splitlines() if x.strip()]
    for i,line in enumerate(lines[:14]):
        m=re.search(r'\bCHAPTER\b',line,re.I)
        if not m:continue
        tail=line[m.end():].strip()
        tail=re.sub(r'^(?:\d+|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)\b\s*','',tail,flags=re.I)
        candidates=([tail] if tail else [])+lines[i+1:i+5]
        pieces=[]
        for value in candidates:
            left=re.split(r'\s{3,}',value)[0].strip()
            if left.isdigit():continue
            if re.match(r'(?i)^(think it over|consider|before |in (?:this|the|class|chapter)|you |we |as you|\d+\.\d+)',left):break
            if len(left.split())>10 or len(left)>100 or not re.search('[A-Za-z]',left):break
            pieces.append(left)
        title=' '.join(pieces).strip()
        if 3<=len(title)<=150:return title
    for line in lines[:6]:
        if line.isupper() and 2<=len(line.split())<=9 and len(line)<=100 and not any(x in line for x in ['TEXTBOOK','REPRINT','UNIT ','PART ']):return line.title()
    return None
