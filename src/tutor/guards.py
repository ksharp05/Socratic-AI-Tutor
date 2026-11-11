"""Input and output guardrails (POC: deterministic rule layer).

Llama Guard 4 is not on the course model list; the model layer is the D-7 classifier (safety_classifier.py,
Gemma 4 31B), called through screen_with_classifier. The rule layer stays in front of it because the course guide
asks for several layers, not one filter, and because it works with no model or key.
"""
from __future__ import annotations

import re
import unicodedata

PII_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"), "[email]"),
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[id-number]"),          # Aadhaar-like
    (re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"), "[phone]"),
    (re.compile(r"\b(my\s+name\s+is|i\s+am\s+called|this\s+is)\s+[A-Z][a-z]+", re.I), r"\1 [name]"),
]
# Explicit self-harm/suicide phrases in English, Hinglish and Hindi (policy TP-D2). Shared with the
# beta chat, which uses only these; bare "die" is never matched so maths wording ("a die is thrown") passes.
_NOT = r"(?:do not|don['’]?t|dont|no longer|never)"
RISK_PATTERN = (
    r"\b(?:"
    r"kill(?:ing)? myself|end(?:ing)? (?:my (?:own )?life|it all)|tak(?:e|ing) my (?:own )?life|"
    r"(?:want|wanna|going|planning|ready) to die|wish i (?:was|were) dead|better off dead|"
    r"wish i (?:had )?never (?:been born|existed)|"
    rf"{_NOT} want to (?:live|be alive|exist|wake up)|"
    r"(?:no|not any|don['’]?t see (?:a|any)) (?:point|reason) (?:in |of )?(?:living|being alive|to live)|"
    r"not worth living|can['’]?t go on (?:living|anymore|like this)|"
    r"(?:hurt(?:ing)?|harm(?:ing)?|cut(?:ting)?) myself|self[- ]?harm\w*|suicid\w*|"
    r"(?:feel|feeling) (?:so |really |completely |totally )?hopeless|"
    r"jee?na nahi|jina nahi|marr? jaa?n[ae]|marr? jaa?u|marna chaht[ai]|khud ?kushi|aa?tmahatya"
    r")\b"
    r"|आत्महत्या|खुदकुशी|मरना चाहत|मर जाना|जीना नहीं"
)
# The core tutor also keeps its broader earlier terms ("hopeless", "can't go on", feeling unsafe).
# "Hopeless at/in/with <subject>" is about schoolwork, not distress (finding 8), so it is excluded;
# "I feel hopeless at school" is still caught by RISK_PATTERN.
_HOPELESS = r"hopeless(?!\s+(?:at|in|with)\b)"
DISTRESS = re.compile(r"\b(?:no reason to live|can'?t go on|" + _HOPELESS + r"|i (?:feel|am) unsafe|"
                      r"i (?:do not|don['’]?t) feel safe|mar jana|jeena nahi)\b|" + RISK_PATTERN, re.I)
ROLE_CLAIM = re.compile(r"\b(i am|i'm|im|this is)\s+(the|your|a)?\s*(teacher|admin|developer|principal)\b", re.I)
KEY_REQUEST = re.compile(r"\b(answer key|answers? to (all|the) (quiz|questions)|show (me )?(the )?answers?|"
                         r"give me (the )?(final )?answer|solutions? (manual|key))\b", re.I)
INJECTION = re.compile(r"(ignore (all |the )?(previous|above|prior) (instructions|rules)|disregard (your|the) rules|"
                       r"you are now|system prompt|reveal (the|your) (prompt|instructions)|act as (an? )?(admin|teacher)|"
                       r"print (all )?(the )?(answers?|keys?))", re.I)
LEAK_PHRASES = re.compile(r"\b(the (final )?answers? (is|are)|the roots are|so x = .* (and|or) x =)", re.I)

HANDOFF_MESSAGE = ("I'm really sorry you're feeling this way. You don't have to handle it alone. Please talk to an "
                   "adult you trust right now, like a parent, teacher or school counsellor. You can also call "
                   "Tele-MANAS, India's free 24x7 mental health helpline, on 14416 or 1-800-891-4416. "
                   "Please tell a trusted adult directly; this chat cannot confirm that anyone has been notified.")


def unverified_own_problem(text: str) -> bool:
    """Flag common user-supplied maths problems; this conservative rule is not exhaustive."""
    normal = " ".join(unicodedata.normalize("NFKC", text).split())
    has_variable = bool(re.search(r"(?i)(?<![a-z])[a-z](?:\s*(?:\^|\*\*)?\s*\d+)?(?![a-z])", normal))
    explicit_task = bool(re.search(r"(?i)\b(?:solve|calculate|evaluate|find|determine|what is|what are)\b", normal))
    explicit_variable = bool(re.search(r"(?i)(?<![a-z])[xyz](?:\s*(?:\^|\*\*)?\s*\d+)?(?![a-z])", normal))
    named_homework = bool(re.search(r"(?i)\b(?:my|this|our)\s+(?:homework|question|problem|exercise)\b", normal))
    return bool(named_homework or ("=" in normal and has_variable) or
                (explicit_task and (explicit_variable or re.search(r"\d|=", normal))))


def screen_input(text: str) -> dict:
    """Return the redacted text plus flags. Pasted text is treated as data, never as instructions."""
    normal = unicodedata.normalize("NFKC", text)
    redacted, pii = normal, []
    for pattern, repl in PII_PATTERNS:
        if pattern.search(redacted):
            pii.append(repl)
            redacted = pattern.sub(repl, redacted)
    # Analyse a flat copy; retain line breaks in the redacted message and maths.
    flag_text = " ".join(normal.split())
    return {
        "text": redacted,
        "pii_redacted": pii,
        "distress": bool(DISTRESS.search(flag_text)),
        "role_claim": bool(ROLE_CLAIM.search(flag_text)),
        "key_request": bool(KEY_REQUEST.search(flag_text)),
        "injection": bool(INJECTION.search(flag_text)),
        "unverified_own_problem": unverified_own_problem(normal),
    }


def screen_with_classifier(text: str, llm, *, session_id: str | None = None, history=()) -> dict:
    """screen_input, then the D-7 classifier on the redacted text when no fixed handoff applies.

    Distress goes straight to the handoff with no model call. Otherwise "classifier" holds the category, route
    ("teach", "policy" or "crisis") and allowed; with the classifier off it is {"source": "off", "allowed": True}.
    """
    from .safety_classifier import classify

    flags = screen_input(text)
    if flags["distress"]:
        flags["classifier"] = {"source": "screen", "category": "self_harm", "route": "crisis", "allowed": False}
        return flags
    flags["classifier"] = classify(flags["text"], llm, session_id=session_id, history=history)
    return flags


def check_citations(text: str, retrieved_ids: set[str]) -> dict:
    cited = set(re.findall(r"\[((?:normalized|ncert|exemplar):[\w.:-]+)\]", text))
    unknown = sorted(cited - retrieved_ids)
    return {"ok": not unknown, "cited": sorted(cited), "unknown": unknown}


def generic_leak(text: str) -> bool:
    return bool(LEAK_PHRASES.search(text))
