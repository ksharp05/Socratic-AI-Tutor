"""Provisional statement evidence from the public misconception catalogue.

These rules identify an explicit claimed step to ask about. Topic words, correct
statements and ordinary questions do not establish a misconception. No simulator,
learner cards, answer keys or held-out records are read here.
"""
from __future__ import annotations

import re

# Each expression describes an incorrect claim in the public catalogue, rather
# than merely naming a topic. These are candidate rules pending R3/R2 review.
STATEMENT_PATTERNS = {
    'ap_m01': [r'(?:constant ratio|doubl\w*|multipl\w*).{0,70}(?:makes? (?:it |an? )?(?:ap|arithmetic)|(?:is|label\w*|call\w*) (?:an? )?ap)',
               r'\b(?:ap|arithmetic progression)\b.{0,65}(?:because|since).{0,40}(?:doubl\w*|constant ratio|multipl\w*)'],
    'ap_m02': [r'(?:common difference|\bd\b).{0,40}(?:earlier|previous|first).{0,15}minus.{0,15}(?:later|next|second)',
               r'(?:positive|revers\w*).{0,45}(?:revers\w*|subtraction).{0,30}(?:subtraction|difference|\bd\b)',
               r'\bd\b.{0,25}(?:positive).{0,30}revers\w*'],
    'ap_m03': [r'\ba\s*\+\s*n\s*\*?\s*d\b', r'(?:formula|term).{0,25}\ba\s*\+\s*d\b.{0,25}\bn\s*=\s*1\b',
               r'(?:nth term|term n).{0,40}\bn (?:jumps|gaps|steps)\b'],
    'ap_m04': [r'(?:total|sum|savings).{0,60}(?:last (?:term|deposit) only|(?:equals?|is) (?:the )?last (?:term|deposit))',
               r'(?:last (?:term|deposit)).{0,35}(?:is|gives|equals).{0,20}(?:the )?(?:sum|total)'],
    'ap_m05': [r'(?:ap|arithmetic progression).{0,30}(?:must|has to|always).{0,30}(?:increase|positive)',
               r'(?:constant|decreas\w*).{0,35}(?:cannot|can.t|is not|isn.t|not an?|reject\w*).{0,20}\bap\b',
               r'(?:constant|decreas\w*) sequence is rejected'],
    'ap_m06': [r'(?:fractional|non.?integer|decimal).{0,25}(?:index|position|term number).{0,30}(?:valid|allowed|acceptable|fine)',
               r'\bn\s*=\s*\d+\.\d+.{0,40}(?:accepted|valid|allowed|term number)'],
    'ap_m07': [r'(?:term values|term difference|difference of (?:the )?terms).{0,50}(?:common difference|one jump).{0,35}(?:regardless|ignore|without)',
               r'(?:ignore|skip).{0,20}(?:index|position) gap.{0,25}(?:difference|\bd\b)'],
    'ap_m08': [r'(?:number|count) of (?:the )?terms.{0,20}(?:end|last)\s*(?:minus|-)\s*(?:start|first)(?!\s*(?:\+\s*1|plus (?:1|one)))'],
    'ap_m09': [r'(?:middle|\bb\b).{0,30}(?:sqrt|geometric mean).{0,50}\bap\b',
               r'\bap\b.{0,50}(?:middle|\bb\b).{0,20}(?:sqrt|geometric mean)'],
    'ap_m10': [r'(?:square numbers|smooth|familiar).{0,50}(?:declared|must be|necessarily|is an?|makes? it).{0,15}\bap\b',
               r'\bap\b.{0,40}because.{0,30}(?:smooth|familiar|square numbers)'],
    'tr_m01': [r'(?:same|fixed).{0,25}(?:side|opposite|adjacent).{0,50}(?:both|every|either).{0,20}(?:acute )?angles?',
               r'(?:opposite|adjacent).{0,20}(?:never|do not|don.t).{0,15}(?:change|depend)'],
    'tr_m02': [r'\bsin(?:e)?(?:\([^)]*\))?\s*(?:=|is|equals)\s*(?:the )?adjacent\s*(?:/|over|divided by)\s*(?:the )?hypotenuse'],
    'tr_m03': [r'1\s*/\s*sin\([^)]*\)\s*(?:=|is|equals|is replaced by)\s*(?:cos\(|cosine)',
               r'cosine\s+(?:is|equals)\s+(?:the )?reciprocal\s+of\s+sine',
               r'cos\([^)]*\)\s*=\s*1\s*/\s*sin\('],
    'tr_m04': [r'tan\([^)]*\)\s*=\s*cos\([^)]*\)\s*/\s*sin\([^)]*\)',
               r'tangent\s+(?:is|equals)\s+cosine\s+(?:over|divided by)\s+sine'],
    'tr_m05': [r'sin\s*\^\s*2\s*\([^)]*\).{0,35}sin\([^)]*\^\s*2\)',
               r'(?:square|squared).{0,20}(?:sine|sin).{0,25}(?:square|squared).{0,15}(?:angle|theta)'],
    'tr_m06': [r'(?:degree value|degrees).{0,30}(?:unchanged|directly).{0,35}radian',
               r'radian.{0,30}(?:unchanged|directly).{0,35}degree'],
    'tr_m07': [r'zero denominator.{0,35}(?:reported as|gives|equals|is) zero', r'(?:denominator|divid\w* by).{0,10}zero.{0,35}(?:reported as|gives|equals|is) zero'],
    'tr_m08': [r'(?:all sides|triangle|side lengths).{0,35}(?:doubl\w*|scal\w*).{0,45}(?:sine|cosine|tangent|ratio).{0,20}(?:also |is )?(?:doubl\w*|scal\w*)'],
    'tr_m09': [r'\(sin\([^)]*\)\s*\+\s*cos\([^)]*\)\)\s*\^2.{0,25}sin\s*\^2\([^)]*\)\s*\+\s*cos\s*\^2\([^)]*\)',
               r'(?:square|squared).{0,20}(?:sum).{0,30}(?:no cross term|sum of (?:the )?squares)'],
    'tr_m10': [r'(?:agreement|agree|works?|true).{0,25}(?:45|one angle|a single angle).{0,40}(?:proof|proves|every angle|all angles)'],
}

CORRECT_NEGATIONS = re.compile(r"\b(?:is not true|isn.t true|do not believe|don.t believe|do not think|don.t think|must not|should not|never assume|need not|does not always|not necessarily)\b", re.I)
QUESTION_START = re.compile(r'^(?:is|are|can|could|what|why|how|does|do|which)\b', re.I)


def candidates(text: str, chapter: str, available_ids: set[str]) -> list[str]:
    text = ' '.join(text.replace('²', '^2').replace('θ', 'theta').replace('−', '-').lower().split())[:10000]
    # A learner explicitly correcting a claim should not inherit the earlier error.
    text = re.split(r'\b(?:but|however|actually|now i (?:know|understand))\b', text)[-1].strip()
    if not text or CORRECT_NEGATIONS.search(text) or (text.endswith('?') and QUESTION_START.match(text)):
        return []
    prefix = {'arithmetic_progressions': 'ap_', 'trigonometry': 'tr_'}.get(chapter)
    if prefix is None:
        return []
    found = [mid for mid, patterns in STATEMENT_PATTERNS.items()
             if mid.startswith(prefix) and mid in available_ids
             and any(re.search(pattern, text, re.I) for pattern in patterns)]
    if prefix == 'ap_':
        gap = re.search(r'a_(\d+)\s*-\s*a_(\d+).{0,30}(?:one|a single) jump', text)
        if gap and abs(int(gap[1]) - int(gap[2])) > 1 and 'ap_m07' in available_ids:
            found.append('ap_m07')
        count = re.search(r'positions? (\d+) (?:through|to) (\d+).{0,35}?(\d+|one|two|three|four|five|six|seven|eight|nine|ten) terms', text)
        if count and 'ap_m08' in available_ids:
            words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten']
            claimed = int(count[3]) if count[3].isdigit() else words.index(count[3])
            if int(count[2]) > int(count[1]) and claimed == int(count[2]) - int(count[1]):
                found.append('ap_m08')
    return list(dict.fromkeys(found))


CORRECTED_STATEMENTS = {
    'ap_m01': r'(?:successive|consecutive|neighbouring) differences (?:must be|are|should be) equal',
    'ap_m02': r'(?:later|second|next) (?:term )?minus (?:the )?(?:earlier|first|previous)',
    'ap_m03': r'n\s*-\s*1.{0,15}(?:gaps|jumps|steps)',
    'ap_m04': r'(?:sum|total).{0,30}(?:all (?:the )?terms|accumulat)',
    'ap_m05': r'(?:ap|arithmetic progression).{0,30}(?:can|may).{0,20}(?:decrease|negative|zero|constant)',
    'tr_m01': r'(?:opposite|adjacent).{0,30}(?:change|depend).{0,25}(?:reference )?angle',
    'tr_m02': r'sine (?:is|equals) (?:the )?opposite (?:over|divided by) (?:the )?hypotenuse',
    'tr_m03': r'(?:reciprocal of sine is (?:cosecant|csc)|cosecant is (?:the )?reciprocal of sine)',
    'tr_m04': r'tangent (?:is|equals) sine (?:over|divided by) cosine',
    'tr_m08': r'(?:sine|ratio|ratios).{0,25}(?:stay|remain|stays|remains) unchanged',
}


def acknowledges_distinction(text: str, mid: str) -> bool:
    """Recognize a few explicit corrections; never grade mastery or resolve a cause."""
    text = ' '.join(text.split())
    pattern = CORRECTED_STATEMENTS.get(mid)
    return bool(pattern and re.search(pattern, text.replace('−', '-'), re.I))
