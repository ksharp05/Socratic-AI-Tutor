"""Bounded side-role checks for registered right-triangle practice."""
import re
import unicodedata
from fractions import Fraction


def check_labels(problem: dict, response: str) -> dict:
    if problem.get('task_type') != 'trig_triangle_ratio':
        return {'status':'unsupported'}
    if not isinstance(response,str) or len(response)>1000:
        return {'status':'clarify'}
    if re.search(r"\b(?:not|isn't|aren't|cannot|can't|don't|doesn't|either|or|false|wrong|incorrect|cm|mm|km|metres?|meters?)\b|[\^*]",response,re.I):
        return {'status':'clarify'}
    angle_pattern=r"\b(?:reference(?:\s+angle)?|angle|using|i\s+used)\s*(?:is|=|:)?\s*([A-Z])\b"
    angles=set(re.findall(angle_pattern,response,re.I))
    remainder=re.sub(angle_pattern,' ',response,flags=re.I)
    angles={a.upper() for a in angles}
    labels={}
    for name in ('opposite','adjacent','hypotenuse'):
        pattern=r'\b'+name+r"(?:\s+side)?\s*(?:is|=|:)?\s*([+-]?\d{1,5}(?:\s*/\s*\d{1,5})?)(?![\d/^*+\-]|\.\d)"
        raw=re.findall(pattern,response,re.I)
        remainder=re.sub(pattern,' ',remainder,flags=re.I)
        try:
            values={Fraction(x.replace(' ','')) for x in raw}
        except (ValueError,ZeroDivisionError):
            return {'status':'clarify'}
        if len(values)!=1 or next(iter(values))<=0:
            return {'status':'clarify'}
        labels[name]=next(iter(values))
    remainder=re.sub(r"\b(?:i think|i used|the|and|my)\b",' ',remainder,flags=re.I)
    if len(angles)!=1 or re.search(r"[^\s,;:.!?]",remainder):
        return {'status':'clarify'}
    givens=problem.get('givens') or {}
    if next(iter(angles)) != givens.get('reference'):
        return {'status':'reference_mismatch'}
    expected = _side_lengths(givens)
    return {'status':'labels_correct' if all(labels[k]==expected[k] for k in labels) else 'labels_mismatch'}


def _side_lengths(givens):
    opposite, adjacent = givens['opposite'], givens['adjacent']
    if givens['reference'] == 'C':
        opposite, adjacent = adjacent, opposite
    return {'opposite': opposite, 'adjacent': adjacent, 'hypotenuse': givens['hypotenuse']}


_RATIO_ROLES = {
    'sin': ('opposite', 'hypotenuse'), 'cos': ('adjacent', 'hypotenuse'),
    'tan': ('opposite', 'adjacent'), 'sec': ('hypotenuse', 'adjacent'),
    'csc': ('hypotenuse', 'opposite'), 'cot': ('adjacent', 'opposite'),
}
_RATIO_NAMES = {
    'sin': ('sin', 'sine', 'साइन'), 'cos': ('cos', 'cosine', 'कोसाइन', 'कॉस'),
    'tan': ('tan', 'tangent', 'टैन', 'टैन्जेंट'), 'sec': ('sec', 'secant'),
    'csc': ('csc', 'cosec', 'cosecant'), 'cot': ('cot', 'cotangent'),
}
_SIDE_NAMES = {
    'opposite': ('opposite', 'सामने वाली भुजा', 'सामने की भुजा', 'सामने वाली side', 'सामने की side', 'सम्मुख भुजा', 'side facing the marked angle',
                 'saamne wali side', 'samne wali side'),
    'adjacent': ('adjacent', 'पास वाली भुजा', 'पास की भुजा', 'आसन्न भुजा',
                 'paas wali side', 'bagal wali side'),
    'hypotenuse': ('hypotenuse', 'longest side', 'longest', 'long side', 'कर्ण',
                   'सबसे लंबी भुजा', 'sabse lambi side'),
}
_TOKEN = r'[\w\u0900-\u0963\u0970-\u097f]'


def _word(pattern):
    return rf'(?<!{_TOKEN})(?:{pattern})(?!{_TOKEN})'


def _aliases(names):
    return {name: key for key, values in names.items() for name in values}


_RATIO_ALIAS = _aliases(_RATIO_NAMES)
_SIDE_ALIAS = _aliases(_SIDE_NAMES)
_RATIO = _word('|'.join(map(re.escape, _RATIO_ALIAS)))
_SIDE = _word('|'.join(map(re.escape, _SIDE_ALIAS)))
_RATIO_PATTERN = re.compile(_RATIO)
_SIDE_SUFFIX = r'(?:\s+(?:side|leg))?(?:\s*\(\s*[a-z]\s*\))?'
_SIDE_PHRASE = rf'{_SIDE}{_SIDE_SUFFIX}'
_FIRST = rf'(?P<first>{_SIDE}){_SIDE_SUFFIX}'
_SECOND = rf'(?P<second>{_SIDE}){_SIDE_SUFFIX}'
_DEFINITE = r'(?:(?:the|my)\s+)?'

# Match relationships that explicitly give the order. Two side names alone do not.
_ORDERED_PAIRS = (
    re.compile(rf'{_FIRST}\s*(?:/|:|\bover\b|\bdivided\s+by\b)\s*{_DEFINITE}{_SECOND}'),
    re.compile(rf'\b(?:divide|divided|dividing)\s+{_DEFINITE}{_FIRST}\s+by\s+{_DEFINITE}{_SECOND}'),
    re.compile(rf'{_FIRST}\s+(?:को|ko)\s+{_SECOND}\s+(?:से|se)\s+{_word("भाग|divide|divided")}'),
)
_POSITIONAL_PAIRS = (
    (re.compile(rf'{_FIRST}\s+(?:on\s+top|in\s+the\s+numerator)\s+and\s+{_DEFINITE}{_SECOND}\s+(?:below|on\s+the\s+bottom|in\s+the\s+denominator)\b'), False),
    (re.compile(rf'{_FIRST}\s+(?:को\s+)?(?:ऊपर|upar)\s+(?:और|aur)\s+{_SECOND}\s+(?:को\s+)?(?:नीचे|neeche|niche)(?!{_TOKEN})'), False),
    (re.compile(rf'{_FIRST}\s+(?:(?:को|ko)\s+)?{_SECOND}\s+(?:के|ke)\s+(?:ऊपर|upar)(?!{_TOKEN})'), False),
    (re.compile(rf'{_FIRST}\s+(?:(?:को|ko)\s+)?{_SECOND}\s+(?:के|ke)\s+(?:नीचे|neeche|niche)(?!{_TOKEN})'), True),
    (re.compile(rf'\b(?:put|placed|wrote)\s+{_DEFINITE}{_FIRST}\s+(?:above|on\s+top\s+of)\s+{_DEFINITE}{_SECOND}'), False),
    (re.compile(rf'\b(?:put|placed|wrote)\s+{_DEFINITE}{_FIRST}\s+(?:under|below|beneath)\s+{_DEFINITE}{_SECOND}'), True),
    (re.compile(rf'{_FIRST}\s+{_word("by")}\s+{_SECOND}(?=\s+{_word("liya|likha|लिया|लिखा")})'), False),
)
_ANGLE_PATTERN = re.compile(
    rf'{_RATIO}(?:\s*\(\s*([a-z])\s*\)|\s+([a-z])\s*(?=[=\d]))|'
    rf'{_word("angle|कोण")}\s+([a-z])(?!{_TOKEN})|{_SIDE}(?:\s+(?:side|leg))?\s*\(\s*([a-z])\s*\)'
)
_MATH_PUNCTUATION = str.maketrans('（）＝／÷∕⁄：', '()=////:')
_OPERATOR = r'[+−\-*/×·^]'
_BEFORE_PAIR_OPERATOR = re.compile(rf'{_OPERATOR}\s*(?:\(\s*)*$')
_AFTER_PAIR_OPERATOR = re.compile(rf'^\s*(?:\)\s*)*(?:{_OPERATOR}|[⁰¹²³⁴⁵⁶⁷⁸⁹])')
_ANGLE_CHANGE_AFTER_PAIR = re.compile(r'\b(?:changed|switched)\s+(?:the\s+)?(?:reference\s+)?angle\b')


def _normalize_step(response):
    text = unicodedata.normalize('NFC', response).casefold()
    return ' '.join(text.replace('’', "'").translate(_MATH_PUNCTUATION).split())

_NEGATION = re.compile(_word(r"not|isn't|aren't|cannot|can't|don't|doesn't|didn't|never|either|or|false|wrong|incorrect|नहीं|नही|मत|या|nahi|nahin|ya"))
_REVIEW_QUESTION = re.compile(r'(?:[,;.!]\s+|\s+)(?:where\s+did\s+i\s+go\s+wrong|galat\s+kya\s+hai)\s*\?\s*$')


# A correction must mark a new clause. Ordinary alternatives still use the
# normal ambiguity checks, and the urgent screen sees the full original turn.
_REVISION = re.compile(
    r'(?:^|[.!?।;,]\s*|\bbut\s+|\blekin\s+|लेकिन\s+|मगर\s+)'
    r'(?:but\s+|lekin\s+|लेकिन\s+)?'
    r'(?:correction\s*:|सुधार\s*:|(?:i meant|mera matlab|मेरा मतलब)\s*:?\s)'
)


_REVISION_HESITATION = re.compile(_word(r'if|maybe|perhaps|shayad|agar|शायद|अगर|यदि'))
_REVISION_SUFFIX = re.compile(r'\s+(?:tha|thi|था|थी)(?=[.!?।]*$)')


def _revision_parts(text):
    corrections = list(_REVISION.finditer(text))
    if not corrections:
        return '', text
    latest = corrections[-1]
    prior_end = corrections[-2].end() if len(corrections) > 1 else 0
    return text[prior_end:latest.start()], _REVISION_SUFFIX.sub('', text[latest.end():].strip())


def _revised_step(text, givens):
    old_step, step = _revision_parts(text)
    if step == text:
        return step, None
    if not step or _REVISION_HESITATION.search(step):
        return step, 'step'
    reference = str(givens.get('reference', '')).lower()
    old_angles = {angle for group in _ANGLE_PATTERN.findall(old_step) for angle in group if angle}
    if old_angles - {reference} and not _ANGLE_PATTERN.search(step):
        return step, 'reference_angle'
    old_names = {_RATIO_ALIAS[name] for name in _RATIO_PATTERN.findall(old_step)}
    if old_names - {givens['ratio']} and not _RATIO_PATTERN.search(step):
        return step, 'target_ratio'
    return step, None


_TOP = _word(r'numerator|अंश')
_BOTTOM = _word(r'denominator|हर')
_SINGLE_POSITION = (
    (re.compile(rf'{_SIDE_PHRASE}\s+(?:को\s+|ko\s+)?(?:on\s+top\b|(?:in\s+the\s+)?{_TOP}|{_word("ऊपर|upar")})|{_TOP}\s+(?:में\s+|mein\s+|is\s+)?{_DEFINITE}{_SIDE_PHRASE}'), 0),
    (re.compile(rf'{_SIDE_PHRASE}\s+(?:को\s+|ko\s+)?(?:on\s+the\s+bottom\b|(?:in\s+the\s+)?{_BOTTOM}|{_word("नीचे|neeche|niche")})|{_BOTTOM}\s+(?:में\s+|mein\s+|is\s+)?{_DEFINITE}{_SIDE_PHRASE}'), 1),
)
_ANGLE_QUESTION = re.compile(r'\b(?:which|what)\s+(?:marked\s+|reference\s+)?angle\b|कौन[- ]सा कोण|किस कोण|\bkaun[- ]?sa\s+angle\b|θ\s+(?:is\s+maybe|शायद)')
_STARTING_QUESTION = re.compile(
    r"""(?:i(?: am|'m) (?:stuck|lost)|i (?:don't|do not) know (?:where|how) to start|"""
    r"""(?:where|how) (?:do|should) i start|i haven'?t started(?: yet)?|"""
    r"""mujhe samajh nahi aa raha (?:kahan|kahaan) se shuru karun|"""
    r"""(?:kahan|kahaan) se shuru karun|मुझे समझ नहीं आ रहा(?: है)? कि कहाँ से शुरू करूँ|कहाँ से शुरू करूँ)"""
)
_DISCOURAGED = re.compile(
    r"""i(?: am|'m) (?:hopeless|terrible|bad) at (?:trigonometry|trig|maths|math)"""
    r"""|mujhse (?:trigonometry|trig|maths) nahi hoti"""
    r"""|मुझसे (?:त्रिकोणमिति|गणित) नहीं होती"""
)
_OPPOSITE_QUESTION = re.compile(
    r"""(?:(?:i (?:don't|do not) (?:understand|know) |can you tell me )?which side is opposite"""
    r"""(?: (?:the |my )?(?:marked |reference )?angle)?|"""
    r"""(?:opposite (?:side|wali side) kaunsi hai|kaunsi side opposite hai)|"""
    r"""(?:चिह्नित कोण के सामने कौन-सी भुजा है|सामने वाली भुजा कौन-सी है))"""
)
_STUDY_STRESS = re.compile(
    r"""i(?: am|'m) (?:stressed|anxious|worried) about (?:my |the )?(?:upcoming )?"""
    r"""(?:test|exam|exams|boards|board exams)"""
)


def _starting_feedback(text):
    question = text.rstrip('.!?।').rstrip()
    for pattern, detail in (
        (_STARTING_QUESTION, 'starting_angle'),
        (_DISCOURAGED, 'discouraged_start'),
        (_OPPOSITE_QUESTION, 'find_opposite'),
        (_STUDY_STRESS, 'study_stress'),
    ):
        if pattern.fullmatch(question):
            return 'clarify', detail
    return None

_UNRESOLVED = re.compile(_word(r"but|instead|unless|rather|लेकिन|मगर|lekin"))
_FRACTION = re.compile(r'\d+(?:\s*[^\W\d_]+)?\s*/\s*\d+')
_INTEGER = r'(?<![\w.+−-])\d{1,5}(?!\d|\.\d)'
_UNIT_ALIASES = {'cm': 'cm', 'सेमी': 'cm', 'mm': 'mm', 'मिमी': 'mm', 'm': 'm', 'मीटर': 'm'}
_UNIT = rf'(?:{"|".join(_UNIT_ALIASES)})(?!{_TOKEN})'
_MEASUREMENT = rf'(?P<value>{_INTEGER})(?:(?:\s*)(?P<unit>{_UNIT})|(?!{_TOKEN}))'
_SINGLE_LENGTH_STEP = re.compile(
    rf"(?:(?:i (?:only |just )?(?:have|got|wrote)|maine(?: bas| sirf)?|"
    rf"(?:मैंने )?(?:अभी )?(?:सिर्फ़?|बस))\s+)?{_INTEGER}\s*{_UNIT}"
    rf"(?:\s+(?:so far|likha(?: hai)?|लिखा(?: है)?))?"
    rf"(?:[,.]?\s+(?:what next|what do i do next|ab kya|अब क्या|आगे))?[.!?।]*"
)
# Recognize what the learner has already supplied without inferring an order.
_COMPARED_SIDES = re.compile(
    rf'\b(?:compare|compares|comparing)\s+{_DEFINITE}{_SIDE_PHRASE}\s+'
    rf'(?:with|and|to)\s+{_DEFINITE}{_SIDE_PHRASE}|'
    rf'{_SIDE_PHRASE}\s+और\s+{_SIDE_PHRASE}\s+का\s+अनुपात'
)
# Hindi may share the noun across both side descriptions.
_HINDI_LEGS = {'सामने वाली': 'opposite', 'सामने की': 'opposite',
               'पास वाली': 'adjacent', 'पास की': 'adjacent'}
_HINDI_LEG = _word('|'.join(_HINDI_LEGS))
_HINDI_SIDE_PAIR = re.compile(
    rf'(?P<first>{_HINDI_LEG})\s+और\s+(?P<second>{_HINDI_LEG})\s+'
    rf'{_word("भुजा|भुजाओं|side")}\s+(?:का|के)\s+{_word("अनुपात|ratio")}'
)

_SIDE_QUESTION = re.compile(
    rf'\b(?:should|can)\s+i\s+use\s+{_DEFINITE}{_SIDE_PHRASE}|'
    rf'{_SIDE_PHRASE}\s+को\s+{_RATIO}\s+में\s+लेना|'
    rf'{_SIDE_PHRASE}\s+{_RATIO}\s+(?:में\s+आएगी\s+ना|mein\s+aayegi\s+na\b)|'
    rf'{_SIDE_PHRASE}\s+{_RATIO}\s+के\s+लिए\s+चाहिए\s+न'
)
_SAME_ROLE_AFTER_ANGLE_CHANGE = re.compile(
    rf'\b(?:changed|switched)\s+(?:the\s+)?(?:reference\s+)?angle\b[^.!?]*?'
    rf'\b(?:kept\s+(?:(?:calling|labelling|labeling)\s+)?|still\s+call\s+)'
    rf'(?:(?:the\s+)?same\s+(?:leg|side)\s+(?:as\s+)?(?:the\s+)?|(?:the\s+)?)'
    rf'{_word("opposite|adjacent")}|'
    rf'कोण\s+बदल\s+दिया.*?{_SIDE}.*?नहीं\s+बदला|'
    rf'\bangle\s+badal\s+gaya\b[^.!?]*?{_word("opposite|adjacent")}(?:\s+side)?\s+same\s+rakh'
)
_CONFLICTING_LABELS = re.compile(
    rf'{_FIRST}\s+(?:is|was)\s+(?:also\s+)?{_DEFINITE}{_SECOND}'
    rf'(?:\s+too\b|(?=[.!?,;]|$))|'
    rf'{_SIDE_PHRASE}\s+ko\s+{_DEFINITE}{_SIDE_PHRASE}\s+bola\b'
)
_QUESTION_WORDS = re.compile(r'\bwhich side\b|कौन[- ]सी भुजा|\bkaunsi side\b')

_ARITHMETIC_NEAR_FRACTION = re.compile(r'[+*÷×^−-]\s*\d|\d\s*[+*÷×^−-]|\d\s*//|//\s*\d')
_NUMERIC_FRACTION = re.compile(rf'{_MEASUREMENT}\s*/\s*{_MEASUREMENT.replace("P<value>", "P<value2>").replace("P<unit>", "P<unit2>")}')
_NUMERIC_ASSIGNMENTS = (
    re.compile(rf'(?P<role>{_SIDE}){_SIDE_SUFFIX}\s+(?:is\s+)?{_MEASUREMENT}'),
    re.compile(rf'{_MEASUREMENT}\s+(?:is\s+|on\s+)?{_DEFINITE}(?P<role>{_SIDE})'),
)


_SETUP_ANGLE = re.compile(
    rf'\b(?:using\s+(?:angle\s+)?|i\s+(?:used|picked|chose)\s+(?:angle\s+)?|'
    rf'(?:reference\s+)?angle\s*(?:is\s+|[=:]\s*)?)([a-z])(?!{_TOKEN})|'
    rf'{_word("कोण")}\s+([a-z])(?!{_TOKEN})'
)
_SETUP_SIDE_ALIAS = {**_SIDE_ALIAS, 'nearby leg': 'adjacent'}
_SETUP_SIDE = _word('|'.join(map(re.escape, _SETUP_SIDE_ALIAS)))
_SETUP_VALUE = rf'(?P<length>{_INTEGER})(?:\s*(?P<unit>{_UNIT}))?(?!{_TOKEN})'
_SETUP_LABEL = rf'(?P<label>{_SETUP_SIDE})(?:\s+(?:side|leg))?'
_SETUP_LABELS = re.compile(
    rf'{_SETUP_LABEL}\s*(?:is\s+|[=:]\s*|\s+){_SETUP_VALUE}|'
    rf'{_SETUP_VALUE.replace("<length>", "<length_first>").replace("<unit>", "<unit_first>")}'
    rf'\s+(?:as\s+)?{_SETUP_LABEL.replace("<label>", "<label_last>")}'
)
_SETUP_FILLER = re.compile(
    r"\b(?:that's what i have in my notes|in that order|i wrote|i think|i labelled|"
    r"for|with|the|and|my|aur|hai)\b|(?:और|हैं|है)"
)
_SETUP_ARITHMETIC = re.compile(r'[+*/÷×^−-]\s*\d|\d\s*[+*/÷×^−-]')


def _label_step_feedback(text, givens):
    """Check an explicit side-label setup before the learner writes a ratio."""
    expected = givens.get('reference')
    if expected not in ('A', 'C') or not {'opposite', 'adjacent', 'hypotenuse'} <= givens.keys():
        return None
    if _SETUP_ARITHMETIC.search(text) or _UNRESOLVED.search(text):
        return None

    angles = set()

    def take_angle(match):
        angles.add((match[1] or match[2]).upper())
        return ' '

    labels = {}
    units = set()

    def take_label(match):
        role = _SETUP_SIDE_ALIAS[match['label'] or match['label_last']]
        labels.setdefault(role, set()).add(int(match['length'] or match['length_first']))
        units.add(_UNIT_ALIASES.get(match['unit'] or match['unit_first']))
        return ' '

    remainder = _SETUP_LABELS.sub(take_label, _SETUP_ANGLE.sub(take_angle, text))
    if not labels:
        return None
    if re.search(r'[^\s.,;:!?।]', _SETUP_FILLER.sub(' ', remainder)):
        return None
    if len(angles) != 1:
        return 'clarify', 'reference_angle'
    if len(units) != 1 or any(len(values) != 1 or 0 in values for values in labels.values()):
        return 'clarify', 'conflicting_labels'
    if angles != {expected}:
        return 'definition_mismatch', 'setup_angle'
    actual = _side_lengths(givens)
    wrong = [role for role, values in labels.items() if values != {actual[role]}]
    if wrong:
        if len(wrong) == 1 and wrong[0] == 'hypotenuse':
            return 'definition_mismatch', 'setup_hypotenuse'
        return 'definition_mismatch', 'setup_labels'
    if len(labels) == len(actual):
        return 'definition_correct', 'setup_complete'
    if len(labels) == len(actual) - 1:
        return 'partial_correct', 'setup_' + next(iter(actual.keys() - labels.keys()))
    return 'partial_correct', 'setup_remaining'

def _numeric_side_pair(text, givens, roles):
    """Resolve a fraction only when both lengths are explicitly identified."""
    if len(roles) != 2 or len(_FRACTION.findall(text)) != 1 or _ARITHMETIC_NEAR_FRACTION.search(text):
        return None, 'side_roles'
    fraction = _NUMERIC_FRACTION.search(text)
    if fraction is None:
        return None, 'side_roles'
    assignments = {}
    units = set()
    for pattern in _NUMERIC_ASSIGNMENTS:
        for match in pattern.finditer(text):
            if match.start() < fraction.end() and fraction.start() < match.end():
                continue
            role = _SIDE_ALIAS[match['role']]
            unit = _UNIT_ALIASES.get(match['unit'])
            assignments.setdefault(role, set()).add(int(match['value']))
            units.add(unit)
    if set(assignments) != roles or any(len(values) != 1 for values in assignments.values()):
        return None, 'side_roles'
    fraction_units = tuple(_UNIT_ALIASES.get(fraction[key]) for key in ('unit', 'unit2'))
    if len(units) != 1 or fraction_units[0] != fraction_units[1]:
        return None, 'side_roles'
    if fraction_units[0] and units != {fraction_units[0]}:
        return None, 'side_roles'
    lengths = {role: next(iter(values)) for role, values in assignments.items()}
    inverse = {value: role for role, value in lengths.items()}
    values = int(fraction['value']), int(fraction['value2'])
    if len(inverse) != 2 or values[0] == values[1] or not set(values) <= inverse.keys():
        return None, 'side_roles'
    if givens.get('reference') not in ('A', 'C') or not all(role in givens for role in {'opposite', 'adjacent', 'hypotenuse'}):
        return None, 'reference_angle'
    expected_lengths = _side_lengths(givens)
    if any(expected_lengths[role] != value for role, value in lengths.items()):
        return None, 'exercise_lengths'
    return (inverse[values[0]], inverse[values[1]]), None


def _unordered_feedback(text, roles, expected, ratio, names):
    """Use only explicit wording to check side choice without grading the ratio."""
    shared_noun = _HINDI_SIDE_PAIR.search(text)
    if shared_noun:
        roles = roles | {_HINDI_LEGS[shared_noun[group]] for group in ('first', 'second')}
    if len(roles) == 2 and names and (shared_noun or _COMPARED_SIDES.search(text)):
        if names != {ratio}:
            return 'definition_mismatch', 'target_ratio'
        return ('partial_correct', 'side_order') if roles == set(expected) else ('definition_mismatch', 'side_roles')
    if len(roles) == 1 and names and _SIDE_QUESTION.search(text):
        if names != {ratio}:
            return 'definition_mismatch', 'target_ratio'
        if not roles <= set(expected):
            return 'definition_mismatch', 'side_roles'
        return 'partial_correct', 'other_side'
    if not roles and _QUESTION_WORDS.search(text):
        return 'clarify', 'side_position'
    return 'clarify', 'side_roles' if roles else 'step'


# The registered right triangles use A and C as their two acute angles.
_COMPLEMENTARY_RATIOS = {'sin': 'cos', 'cos': 'sin', 'tan': 'cot',
                         'cot': 'tan', 'sec': 'csc', 'csc': 'sec'}
_ACUTE_ANGLE = r'(?:\s*\(\s*[ac]\s*\)|\s+[ac])'
_RATIO_AT_ANGLE = rf'{_RATIO}{_ACUTE_ANGLE}'
_STEP_PREFIX = r'(?:(?:i\s+(?:used|wrote)|maine|मैंने)\s+)?'
_EQUIVALENCE = re.compile(
    rf'{_STEP_PREFIX}(?P<left>{_RATIO_AT_ANGLE})\s*=\s*(?P<right>{_RATIO_AT_ANGLE})'
    rf'(?:\s*=\s*(?P<work>.+)|[.!?।]?)'
)
_SIDE_PAIR = (
    rf'{_DEFINITE}(?P<first>{_SIDE})(?:\s+(?:side|leg))?(?:\s*\(\s*(?P<first_angle>[ac])\s*\))?'
    rf'\s*(?:/|:|\bover\b|\bdivided\s+by\b)\s*'
    rf'{_DEFINITE}(?P<second>{_SIDE})(?:\s+(?:side|leg))?(?:\s*\(\s*(?P<second_angle>[ac])\s*\))?'
)
_EXPLICIT_SETUP = re.compile(
    rf'{_STEP_PREFIX}(?P<expression>{_RATIO_AT_ANGLE})\s*=\s*{_SIDE_PAIR}[.!?।]?'
)
_SUBSTITUTION = re.compile(
    rf'{_STEP_PREFIX}(?:(?P<name>{_RATIO})(?P<angle>{_ACUTE_ANGLE}|\s+θ|\s+theta)?\s*=\s*)?'
    rf'{_SIDE_PAIR}\s*=\s*(?P<fraction>.+)'
)
_EQUALITY_AFTER_PAIR = re.compile(r'^\s*(?:\)\s*)*=')


# The registered triangles name A and C as the acute angles. In a learner's
# ABC notation the remaining vertex is B, so AC is the hypotenuse.
_SEGMENT_ROLES = {
    'a': {'ab': 'adjacent', 'bc': 'opposite', 'ac': 'hypotenuse'},
    'c': {'ab': 'opposite', 'bc': 'adjacent', 'ac': 'hypotenuse'},
}
_SEGMENT = r'[a-z]{2}'
_ANGLE_MARK = r'(?:\s*\(\s*[a-zθ]\s*\)|\s+(?:[a-zθ]|theta))'
_NAMED_RATIO = re.compile(
    rf'(?:(?:right angle at (?P<right>[a-z])|(?P<vertex>[a-z]) is the right angle)[.!;,]\s*)?'
    rf'(?P<prefix>{_STEP_PREFIX}(?:{_RATIO}(?:{_ANGLE_MARK})?\s*=\s*){{0,2}})'
    rf'(?P<first>{_SIDE_PHRASE}|{_SEGMENT})\s*(?:/|:|\bover\b)\s*'
    rf'(?P<second>{_SIDE_PHRASE}|{_SEGMENT})(?P<rest>\s*=\s*.+)?'
    rf'(?:\s+(?:likha|liya|लिखा|लिया)(?:\s+(?:hai|है))?)?\s*[.!?।]?'
)
_NAMED_RATIO_ANGLE = re.compile(rf'{_RATIO}(?P<angle>{_ANGLE_MARK})?\s*=')


def _segment_role(label, reference):
    return _SEGMENT_ROLES[reference].get(''.join(sorted(label)))


def _choice_pair(top, bottom):
    return (
        rf'{_DEFINITE}(?P<{top}>{_SIDE}|{_SEGMENT})(?:\s+(?:side|leg))?'
        rf'\s*(?:/|:|\bover\b|\bdivided\s+by\b)\s*'
        rf'{_DEFINITE}(?P<{bottom}>{_SIDE}|{_SEGMENT})(?:\s+(?:side|leg))?'
    )


_FRACTION_CHOICE = re.compile(
    rf"{_STEP_PREFIX}(?:(?:should i use|should it be|is it|"
    rf"i'm not sure whether to use|i am not sure whether to use)\s+)?"
    rf'(?:(?P<ratio>{_RATIO})(?P<angle>{_ANGLE_MARK})?\s*[=:]\s*)?(?:either\s+)?'
    rf'{_choice_pair("top1", "bottom1")}\s+(?:or|ya|या)\s+{_choice_pair("top2", "bottom2")}'
    rf'(?:\s+(?:likha|liya|लिखा|लिया)(?:\s+(?:hai|है))?)?\s*[.!?।]*'
)
_CHOOSE_NUMERATOR = 'choose_numerator'
_CHOOSE_DENOMINATOR = 'choose_denominator'
_FRACTION_CHOICE_QUESTIONS = {_CHOOSE_NUMERATOR, _CHOOSE_DENOMINATOR}


def _fraction_choice_feedback(text, givens, expected):
    """Ask about the side that differs between two explicitly offered fractions."""
    choice = _FRACTION_CHOICE.fullmatch(text)
    if not choice:
        return None
    reference = str(givens.get('reference', '')).lower()
    angle = choice['angle'].strip(' ()') if choice['angle'] else None
    if angle and angle not in (reference, 'θ', 'theta'):
        return 'clarify', 'reference_angle'
    segments = _SEGMENT_ROLES.get(reference, {})
    top1, bottom1, top2, bottom2 = (
        _SIDE_ALIAS.get(choice[key]) or segments.get(''.join(sorted(choice[key])))
        for key in ('top1', 'bottom1', 'top2', 'bottom2')
    )
    if not all((top1, bottom1, top2, bottom2)):
        return None
    if choice['ratio'] and _RATIO_ALIAS[choice['ratio']] != givens['ratio']:
        return 'clarify', 'target_ratio'
    if (top1, bottom1) == (top2, bottom2):
        return _side_pair_verdict((top1, bottom1), expected) if top1 != bottom1 else None
    if bottom1 == bottom2:
        return 'clarify', f'{_CHOOSE_NUMERATOR}:{bottom1}'
    if top1 == top2:
        return 'clarify', f'{_CHOOSE_DENOMINATOR}:{top1}'
    return 'clarify', 'choose_fraction'


def _resolve_segment_ratio(text, givens):
    """Translate a bounded pair of vertex labels into the existing side roles."""
    reference = str(givens.get('reference', '')).lower()
    if reference not in _SEGMENT_ROLES:
        return text, None
    step = _NAMED_RATIO.fullmatch(text)
    if not step:
        return text, None
    sides = step['first'], step['second']
    segments = [side for side in sides if re.fullmatch(_SEGMENT, side)]
    if not any(_segment_role(label, reference) for label in segments):
        return text, None
    if (step['right'] or step['vertex'] or 'b') != 'b':
        return text, 'diagram_angle'
    terms = list(_NAMED_RATIO_ANGLE.finditer(step['prefix']))
    if terms and terms[-1]['angle']:
        angle = terms[-1]['angle'].strip(' ()')
        if angle not in ('θ', 'theta'):
            reference = angle
    if reference not in _SEGMENT_ROLES:
        return text, 'reference_angle'
    roles = [_segment_role(side, reference) if side in segments else side for side in sides]
    if not all(roles):
        return text, 'diagram_labels'
    return f"{step['prefix']}{roles[0]} / {roles[1]}{step['rest'] or ''}", None

def _ratio_at_angle(expression):
    name = _RATIO_PATTERN.match(expression)
    return _RATIO_ALIAS[name[0]], expression[name.end():].strip(' ()')


def _complementary_feedback(text, givens):
    reference = givens.get('reference')
    if reference not in ('A', 'C'):
        return None
    ratio = givens['ratio']
    target = (ratio, reference.lower())
    alternate = (_COMPLEMENTARY_RATIOS[ratio], 'c' if reference == 'A' else 'a')
    equation = _EQUIVALENCE.fullmatch(text)
    if equation:
        terms = {_ratio_at_angle(equation[side]) for side in ('left', 'right')}
        if terms != {target, alternate}:
            if len(terms) == 2 and target in terms:
                return 'definition_mismatch', 'complementary_identity'
            return None
        work = equation['work']
        if work is None:
            return 'definition_correct', 'complementary_identity'
        # The side names in the remaining work refer to the immediately preceding ratio.
        text = f"{equation['right']} = {work}"
        substitution = _substitution_feedback(text, givens, _RATIO_ROLES[ratio])
        if substitution:
            return substitution

    setup = _EXPLICIT_SETUP.fullmatch(text)
    if not setup:
        if equation:
            detail = 'complementary_work' if _NUMERIC_FRACTION.fullmatch(work.rstrip('.!?।').rstrip()) else 'expression'
            return 'clarify', detail
        return None
    term = _ratio_at_angle(setup['expression'])
    if term != alternate and not equation:
        return None
    if any(setup[side] and setup[side] != term[1] for side in ('first_angle', 'second_angle')):
        return 'clarify', 'reference_angle'
    pair = tuple(_SIDE_ALIAS[setup[side]] for side in ('first', 'second'))
    expected = _RATIO_ROLES[term[0]]
    if term == target:
        return _side_pair_verdict(pair, expected)
    if pair == expected:
        return 'definition_correct', 'complementary_setup'
    if pair == expected[::-1]:
        return 'definition_mismatch', 'complementary_order'
    return 'definition_mismatch', 'complementary_sides'


def _side_pair_verdict(pair, expected):
    if pair == expected:
        return 'definition_correct', 'order'
    if pair == expected[::-1]:
        return 'definition_mismatch', 'reversed_order'
    if pair[0] == expected[0]:
        return 'definition_mismatch', 'denominator'
    if pair[1] == expected[1]:
        return 'definition_mismatch', 'numerator'
    return 'definition_mismatch', 'side_roles'


def _substitution_result(givens, pair, text):
    fraction = _NUMERIC_FRACTION.fullmatch(text.rstrip('.!?।').rstrip())
    if fraction is None:
        return 'clarify', 'substitution_fraction'
    units = [_UNIT_ALIASES.get(fraction[field]) for field in ('unit', 'unit2')]
    if units[0] != units[1]:
        return 'clarify', 'substitution_units'
    values = tuple(int(fraction[field]) for field in ('value', 'value2'))
    if min(values) <= 0:
        return 'clarify', 'substitution_fraction'
    sides = _side_lengths(givens)
    lengths = tuple(sides[role] for role in pair)
    if values == lengths:
        return 'definition_correct', 'substitution'
    if values == lengths[::-1]:
        return 'definition_mismatch', 'substitution_order'
    if values[0] * lengths[1] == values[1] * lengths[0]:
        return 'definition_correct', 'equivalent_fraction'
    if values[0] == lengths[0]:
        return 'definition_mismatch', 'substitution_denominator'
    if values[1] == lengths[1]:
        return 'definition_mismatch', 'substitution_numerator'
    return 'definition_mismatch', 'substitution_values'


def _substitution_feedback(text, givens, expected):
    reference = givens.get('reference')
    if reference not in ('A', 'C') or not {'opposite', 'adjacent', 'hypotenuse'} <= givens.keys():
        return None
    setup = _SUBSTITUTION.fullmatch(text)
    if setup is None:
        return None
    ratio = givens['ratio']
    named = _RATIO_ALIAS[setup['name']] if setup['name'] else ratio
    angle = (setup['angle'] or '').strip(' ()')
    alternate = angle in ('a', 'c') and angle != reference.lower()
    if alternate and named != _COMPLEMENTARY_RATIOS[ratio]:
        return 'clarify', 'reference_angle'
    if not alternate and named != ratio:
        return 'definition_mismatch', 'target_ratio'
    active_angle = angle if alternate else reference.lower()
    if any(setup[k] and setup[k] != active_angle for k in ('first_angle', 'second_angle')):
        return 'clarify', 'reference_angle'
    pair = tuple(_SIDE_ALIAS[setup[k]] for k in ('first', 'second'))
    expected = _RATIO_ROLES[named] if alternate else expected
    if pair != expected:
        if alternate:
            return 'definition_mismatch', 'complementary_order' if pair == expected[::-1] else 'complementary_sides'
        return _side_pair_verdict(pair, expected)
    return _substitution_result({**givens, 'reference': active_angle.upper()}, pair, setup['fraction'])

def ratio_step_feedback(problem: dict, response: str, *, check_values=True) -> tuple[str, str]:
    """Return a side-role verdict and the detail needed for the next hint."""
    if problem.get('task_type') != 'trig_triangle_ratio':
        return 'unsupported', 'exercise'
    givens = problem.get('givens') or {}
    expected = _RATIO_ROLES.get(givens.get('ratio'))
    if expected is None:
        return 'unsupported', 'exercise'
    if not isinstance(response, str) or len(response) > 1000:
        return 'clarify', 'step'
    text = _normalize_step(response)
    if not text:
        return 'clarify', 'step'
    text = _REVIEW_QUESTION.sub('', text)
    if check_values:
        text, revision_issue = _revised_step(text, givens)
        if revision_issue:
            return 'clarify', revision_issue
        starting = _starting_feedback(text)
        if starting:
            return starting
        if _SINGLE_LENGTH_STEP.fullmatch(text):
            return 'clarify', 'length_side'
        text, diagram_issue = _resolve_segment_ratio(text, givens)
        if diagram_issue:
            return 'clarify', diagram_issue
        substitution = _substitution_feedback(text, givens, expected)
        if substitution:
            return substitution
        alternate = _complementary_feedback(text, givens)
        if alternate:
            return alternate
    if check_values and not _RATIO_PATTERN.search(text) and not _NEGATION.search(text):
        label_feedback = _label_step_feedback(text, givens)
        if label_feedback:
            return label_feedback
    names = {_RATIO_ALIAS[name] for name in _RATIO_PATTERN.findall(text)}
    if len(names) > 1:
        return 'clarify', 'target_ratio'
    angles = {angle for group in _ANGLE_PATTERN.findall(text) for angle in group if angle}
    if (angles and angles != {str(givens.get('reference', '')).casefold()}) or _ANGLE_QUESTION.search(text):
        return 'clarify', 'reference_angle'
    if check_values:
        change = _SAME_ROLE_AFTER_ANGLE_CHANGE.search(text)
        if change and not _NEGATION.search(text[:change.start()]):
            return 'definition_mismatch', 'relabel_angle'
        labels = _CONFLICTING_LABELS.search(text)
        if labels and len({_SIDE_ALIAS[role] for role in re.findall(_SIDE, labels[0])}) > 1:
            return 'clarify', 'conflicting_labels'
    if check_values:
        choice = _fraction_choice_feedback(text, givens, expected)
        if choice:
            return choice
    if _NEGATION.search(text):
        return 'clarify', 'step'

    def read_pair(match, reverse=False):
        first, second = (_SIDE_ALIAS[match[group]] for group in ('first', 'second'))
        return (second, first) if reverse else (first, second)

    # Key by role positions so multiple patterns can recognize the same pair.
    # Repeating a pair elsewhere stays ambiguous.
    pairs = {}
    for pattern, reverse in (*((pattern, False) for pattern in _ORDERED_PAIRS),
                             *_POSITIONAL_PAIRS):
        for match in pattern.finditer(text):
            positions = match.start('first'), match.start('second')
            pairs.setdefault(positions, (read_pair(match, reverse), match.span()))
    roles = {_SIDE_ALIAS[name] for name in re.findall(_SIDE, text)}
    numeric = False
    if not pairs:
        if _FRACTION.search(text):
            if not check_values:
                return 'clarify', 'side_roles'
            pair, missing = _numeric_side_pair(text, givens, roles)
            if pair is None:
                return 'clarify', missing
            numeric = True
        elif len(roles) == 1:
            positions = [position for pattern, position in _SINGLE_POSITION if pattern.search(text)]
            if not positions and check_values and not _UNRESOLVED.search(text):
                return _unordered_feedback(text, roles, expected, givens['ratio'], names)
            if len(positions) != 1:
                return 'clarify', 'side_roles'
            position = positions[0]
            if names and names != {givens['ratio']}:
                return 'definition_mismatch', 'target_ratio'
            if not check_values:
                return 'clarify', ('denominator', 'numerator')[position]
            if next(iter(roles)) == expected[position]:
                return 'partial_correct', ('denominator', 'numerator')[position]
            return 'definition_mismatch', ('numerator', 'denominator')[position]
        elif check_values and not _UNRESOLVED.search(text):
            return _unordered_feedback(text, roles, expected, givens['ratio'], names)
        else:
            return 'clarify', 'side_roles' if roles else 'step'
    elif len(pairs) != 1:
        return 'clarify', 'step'
    else:
        pair, (start, end) = next(iter(pairs.values()))
        if _BEFORE_PAIR_OPERATOR.search(text[:start]) or _AFTER_PAIR_OPERATOR.match(text[end:]):
            return 'clarify', 'expression'
        if check_values and _ANGLE_CHANGE_AFTER_PAIR.search(text, end):
            return 'clarify', 'reference_angle'
        if check_values and _FRACTION.search(text):
            return 'clarify', 'side_roles'
        if check_values and _EQUALITY_AFTER_PAIR.match(text[end:]):
            return 'clarify', 'substitution_fraction'
        if _UNRESOLVED.search(text, start):
            return 'clarify', 'step'
        if pair[0] == pair[1] or not roles <= set(pair):
            return 'clarify', 'side_roles'
    if names and names != {givens['ratio']}:
        return 'definition_mismatch', 'target_ratio'
    if numeric and pair == expected:
        return 'definition_correct', 'substitution'
    return _side_pair_verdict(pair, expected)


_SUBSTITUTION_REPAIRS = {
    'mismatch_substitution_order': 0,
    'mismatch_substitution_numerator': 0,
    'mismatch_substitution_denominator': 1,
}
_SUBSTITUTION_QUESTIONS = {
    'order', 'complementary_setup', 'substitution_fraction', 'substitution_units', 'partial_substitution_numerator',
    'mismatch_substitution_values', *_SUBSTITUTION_REPAIRS,
}


_SIDE_SELECTION_QUESTIONS = {
    'fraction_side_roles', 'setup_complete', 'mismatch_side_roles', 'partial_target_ratio',
    'length_ratio_sides',
}
_FOLLOWUP_SIDE_PAIR = re.compile(
    rf'{_DEFINITE}(?:side\s+)?(?P<first>{_SIDE}|{_SEGMENT})(?:\s+(?:side|leg))?'
    rf'(?:\s*\(\s*(?P<first_angle>[a-z])\s*\))?\s+(?:and|aur|और)\s+'
    rf'{_DEFINITE}(?:side\s+)?(?P<second>{_SIDE}|{_SEGMENT})(?:\s+(?:side|leg))?'
    rf'(?:\s*\(\s*(?P<second_angle>[a-z])\s*\))?'
)

def ratio_followup_feedback(problem: dict, response: str, question: str) -> tuple[str, str] | None:
    """Interpret a short answer only in the context of a specific question."""
    if problem.get('task_type') != 'trig_triangle_ratio':
        return None
    givens = problem.get('givens') or {}
    expected = _RATIO_ROLES.get(givens.get('ratio'))
    if not expected:
        return None
    text = _normalize_step(response).rstrip('.!?।').rstrip()
    if question in _SUBSTITUTION_QUESTIONS and givens.get('reference') in ('A', 'C') and _SIDE_NAMES.keys() <= givens.keys():
        if _NUMERIC_FRACTION.fullmatch(text):
            return _substitution_result(givens, expected, text)
        position = _SUBSTITUTION_REPAIRS.get(question)
        length = re.fullmatch(_MEASUREMENT, text) if position is not None else None
        if length and length['unit'] is None:
            if int(length['value']) == _side_lengths(givens)[expected[position]]:
                if question == 'mismatch_substitution_order':
                    return 'partial_correct', 'substitution_numerator'
                return 'definition_correct', 'substitution'
            return 'definition_mismatch', question.removeprefix('mismatch_')
    if question in ('reference_angle', 'mismatch_setup_angle'):
        match = re.fullmatch(r'(?:angle\s+|कोण\s+)?([a-z])', text)
        if match:
            if match[1].upper() == givens.get('reference'):
                return 'partial_correct', 'reference_angle'
            return 'definition_mismatch', 'setup_angle'
        return None
    if question in ('target_ratio', 'mismatch_target_ratio'):
        ratio = _RATIO_PATTERN.fullmatch(text)
        if ratio:
            if _RATIO_ALIAS[ratio[0]] == givens['ratio']:
                return 'partial_correct', 'target_ratio'
            return 'definition_mismatch', 'target_ratio'
        return None
    if question == 'side_position':
        position = {'numerator': 'numerator', 'denominator': 'denominator',
                    'top': 'numerator', 'bottom': 'denominator', 'upar': 'numerator',
                    'neeche': 'denominator', 'niche': 'denominator',
                    'अंश': 'numerator', 'हर': 'denominator'}.get(text)
        return ('clarify', position) if position else None
    setup, _, context = question.partition(':')
    if setup in ('partial_setup_opposite', 'partial_setup_adjacent', 'partial_setup_hypotenuse'):
        role = setup.removeprefix('partial_setup_')
        length = re.fullmatch(_MEASUREMENT, text)
        if length and {'opposite', 'adjacent', 'hypotenuse'} <= givens.keys():
            unit = _UNIT_ALIASES.get(length['unit'])
            if (unit is None or unit == context) and int(length['value']) == _side_lengths(givens)[role]:
                return 'definition_correct', 'setup_complete'
            return 'clarify', setup.removeprefix('partial_')
        return None
    positions = {
        'partial_numerator': (0, True), 'partial_denominator': (1, True),
        'partial_side_order': (0, True), 'reversed_order': (0, True),
        'numerator': (0, False), 'denominator': (1, False),
        'mismatch_numerator': (0, False), 'mismatch_denominator': (1, False),
        'partial_reference_angle': (0, False),
    }
    if question in _SIDE_SELECTION_QUESTIONS:
        sides = _FOLLOWUP_SIDE_PAIR.fullmatch(text)
        if sides:
            reference = str(givens.get('reference', '')).lower()
            segments = _SEGMENT_ROLES.get(reference, {})
            chosen = {
                _SIDE_ALIAS.get(label) or segments.get(''.join(sorted(label)))
                for label in (sides['first'], sides['second'])
            }
            if chosen == {None}:
                return None
            if any(angle and angle != reference for angle in (sides['first_angle'], sides['second_angle'])):
                return 'clarify', 'reference_angle'
            if None in chosen:
                return 'clarify', 'diagram_labels'
            return ('partial_correct', 'side_order') if chosen == set(expected) else ('definition_mismatch', 'side_roles')
    choice = re.fullmatch(
        r"(?:(?:it\s+is|it's|i\s+used|i\s+put|maine)\s+)?"
        rf'{_DEFINITE}(?P<side>{_SIDE})(?:\s+(?:side|leg))?',
        text,
    )
    if choice:
        side = _SIDE_ALIAS[choice['side']]
    else:
        segment = re.fullmatch(r'(?:the )?(?:side (?P<side>[a-zA-Z]{2})|(?P<bare>[A-Z]{2}))[.!?]?',
                               response.strip())
        reference = str(givens.get('reference', '')).lower()
        # A bare lowercase diagram label is meaningful when answering a side question.
        label = (segment['side'] or segment['bare']).lower() if segment else text
        if reference not in _SEGMENT_ROLES or (not segment and not _segment_role(label, reference)):
            return None
        if question == 'mismatch_complementary_order':
            reference = 'c' if reference == 'a' else 'a'
        side = _segment_role(label, reference)
        if side is None:
            return 'clarify', question if setup in _FRACTION_CHOICE_QUESTIONS or question == 'length_side' else 'diagram_labels'
        if question == 'find_opposite':
            if side == 'opposite':
                return 'partial_correct', 'opposite_identified'
            return 'clarify', 'find_opposite'
    if question == 'length_side':
        if side in expected:
            return 'clarify', 'length_other_side:' + side
        return 'clarify', 'length_ratio_sides'
    if setup in _FRACTION_CHOICE_QUESTIONS:
        if side == context or context not in _SIDE_NAMES:
            return 'clarify', question
        pair = (side, context) if setup == _CHOOSE_NUMERATOR else (context, side)
        return _side_pair_verdict(pair, expected)
    if question == 'mismatch_complementary_order' and givens.get('reference') in ('A', 'C'):
        numerator, _ = _RATIO_ROLES[_COMPLEMENTARY_RATIOS[givens['ratio']]]
        if side == numerator:
            return 'definition_correct', 'complementary_setup'
        return 'clarify', 'retry_complementary_order'
    if question in _SIDE_SELECTION_QUESTIONS:
        return ('partial_correct', 'other_side') if side in expected else ('definition_mismatch', 'side_roles')
    if question.startswith('partial_other_side:'):
        known = question.split(':', 1)[1]
        if known in expected and side in expected and side != known:
            return 'partial_correct', 'side_order'
        return 'clarify', 'other_side'
    if question in positions:
        index, completes_order = positions[question]
        position, other = ('numerator', 'denominator')[index], ('denominator', 'numerator')[index]
        if side != expected[index]:
            return 'clarify', 'retry_' + position
        if completes_order:
            return 'definition_correct', 'order'
        return 'partial_correct', other
    return None


def ratio_followup_question(key: str, response: str) -> str | None:
    if key in ('starting_angle', 'discouraged_start', 'study_stress'):
        return 'reference_angle'
    if key == 'partial_opposite_identified':
        return 'numerator'
    question, _, context = key.partition(':')
    if question == 'length_other_side':
        return 'partial_other_side:' + context
    if key in ('find_opposite', 'length_side') or question in _FRACTION_CHOICE_QUESTIONS:
        return key
    if key in ('side_roles', 'partial_other_side', 'partial_setup_opposite',
               'partial_setup_adjacent', 'partial_setup_hypotenuse'):
        _, text = _revision_parts(_normalize_step(response))
    if key == 'side_roles' and _FRACTION.search(text) and not re.search(_SIDE, text):
        return 'fraction_side_roles'
    if key == 'partial_other_side':
        sides = {_SIDE_ALIAS[side] for side in re.findall(_SIDE, text)}
        if len(sides) == 1:
            return 'partial_other_side:' + sides.pop()
        return None
    if key in ('partial_setup_opposite', 'partial_setup_adjacent', 'partial_setup_hypotenuse'):
        units = {_UNIT_ALIASES.get(m['unit'] or m['unit_first']) for m in _SETUP_LABELS.finditer(text)}
        unit = next(iter(units)) if len(units) == 1 else None
        return f'{key}:{unit}' if unit else key
    if key in {
        'reference_angle', 'mismatch_setup_angle', 'side_position', 'partial_numerator',
        'partial_denominator', 'partial_side_order', 'reversed_order', 'numerator', 'denominator',
        'mismatch_numerator', 'mismatch_denominator', 'partial_reference_angle',
        'mismatch_complementary_order', 'target_ratio', 'mismatch_target_ratio',
        *_SIDE_SELECTION_QUESTIONS, *_SUBSTITUTION_QUESTIONS,
    }:
        return key
    return None

def check_ratio_definition(problem: dict, response: str) -> dict:
    """Check an ordered pair of side names without evaluating their lengths."""
    status, _ = ratio_step_feedback(problem, response, check_values=False)
    return {'status': status}
