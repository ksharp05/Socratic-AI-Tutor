"""Text repair for extracted NCERT pages and the maths tokenizer used by every BM25 index.

The NCERT PDFs set operators and Greek letters in the Symbol font. Both extractors in spike S3 return
those glyphs as Private Use Area code points U+F0xx (the Symbol-font code plus 0xF000), so `a ≠ 0`
comes out as `a \\uf0b9 0`. `repair_symbols` maps them back. Formulas in extracted text are still
unreliable (fractions lose their layout), which is why TP-T2 says formulas are cited from cards only.
"""
from __future__ import annotations

import re
import unicodedata

from bm25s.stopwords import STOPWORDS_EN

# Adobe Symbol encoding, for the codes seen in chapters 4, 5 and 8 (and a few likely neighbours).
_SYMBOL = {
    0x28: "(", 0x29: ")", 0x2B: "+", 0x2D: "−", 0x2E: ".", 0x2F: "/", 0x3C: "<", 0x3D: "=", 0x3E: ">",
    0x40: "≅", 0x44: "Δ", 0x5B: "[", 0x5D: "]", 0x61: "α", 0x62: "β", 0x64: "δ", 0x66: "φ", 0x67: "γ",
    0x6C: "λ", 0x70: "π", 0x71: "θ", 0x73: "σ", 0xA3: "≤", 0xA5: "∞", 0xB0: "°", 0xB1: "±", 0xB3: "≥",
    0xB4: "×", 0xB9: "≠", 0xD0: "∠", 0xD6: "√", 0xD7: "·",
}
# Glyphs that only draw brackets, braces or radical bars; they carry no text.
_DECORATION = set(range(0xE6, 0xF0)) | set(range(0xF6, 0xFF)) | {0x34}


def repair_symbols(text: str) -> str:
    def fix(match: re.Match) -> str:
        code = ord(match.group(0)) - 0xF000
        if code in _SYMBOL:
            return _SYMBOL[code]
        if code in _DECORATION:
            return " "
        if 0x30 <= code <= 0x39:
            return chr(code)
        return " "
    return re.sub("[-]", fix, text)


_MATH = [("²", "^2"), ("³", "^3"), ("θ", " theta "), ("√", " sqrt "), ("±", " pm "), ("≠", " neq "),
         ("≤", " leq "), ("≥", " geq "), ("π", " pi "), ("∠", " angle "), ("Δ", " delta "), ("α", " alpha "),
         ("°", " degree "), ("–", "-"), ("−", "-")]
_TOKEN = re.compile(r"[a-z]+(?:_[a-z0-9]+)?(?:\^\d+)?|\d+")
STOPWORDS = set(STOPWORDS_EN) | {"do", "does", "did", "can", "i", "my", "how", "what", "which", "why", "when",
                                  "should", "would", "could", "may", "might", "get", "use", "still"}


def _stem(token: str) -> str:
    """A deliberately light stemmer: plural -s/-es and -ing/-ed, so 'roots' matches 'root'."""
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 5 and token.endswith("ing"):
        return token[:-3]
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


_RATIO_NAMES = {"sine": "sin", "cosine": "cos", "tangent": "tan", "secant": "sec",
                "cosecant": "csc", "cosec": "csc", "cotangent": "cot"}
_RATIO_PATTERN = re.compile(r"\b(" + "|".join(_RATIO_NAMES) + r")\b", re.I)


def normalise_ratio_names(text: str) -> str:
    """Use the same ratio spelling in queries and indexed formulas; match whole words."""
    return _RATIO_PATTERN.sub(lambda match: _RATIO_NAMES[match.group().lower()], text)


def normalise(text: str) -> str:
    text = repair_symbols(text)
    for src, dst in _MATH:
        text = text.replace(src, dst)
    text = normalise_ratio_names(unicodedata.normalize("NFKC", text).lower())
    return text.replace("x-squared", "x^2").replace("squared", "^2")


def tokenize(text: str) -> list[str]:
    """Maths-aware tokens: keeps `a_n`, `s_n` and `b^2`; maps θ, √, ±, ≠ and ² to words."""
    return [_stem(t) for t in _TOKEN.findall(normalise(text)) if t not in STOPWORDS]
