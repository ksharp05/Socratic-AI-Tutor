"""Input and output guardrails (POC: deterministic rule layer).

Prompt Guard 2 and Llama Guard 4 slot in as further layers once model access is confirmed; the rule layer
stays because the course guide asks for several layers, not one filter.
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
DISTRESS = re.compile(r"\b(kill myself|end my life|want to die|hurt myself|self[- ]harm|suicid\w*|no reason to live|"
                      r"can'?t go on|hopeless|i (?:feel|am) unsafe|i (?:do not|don['’]?t) feel safe|mar jana|jeena nahi)\b", re.I)
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


def check_citations(text: str, retrieved_ids: set[str]) -> dict:
    cited = set(re.findall(r"\[((?:normalized|ncert|exemplar):[\w.:-]+)\]", text))
    unknown = sorted(cited - retrieved_ids)
    return {"ok": not unknown, "cited": sorted(cited), "unknown": unknown}


def generic_leak(text: str) -> bool:
    return bool(LEAK_PHRASES.search(text))
