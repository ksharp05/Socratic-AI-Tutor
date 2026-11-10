"""Deterministic safety layer for the beta chat (no model call, no key).

Ported from the security test's hardened front door (scripts/qa/hardened_front_door.py, v4), 10 November 2026:
- clean_text removes invisible control, bidi, tag and smuggling characters before storage or a model call, keeping
  the zero-width joiners that Devanagari needs and leaving maths symbols such as x² unchanged (no NFKC).
- screening_text builds a separate copy for matching only: NFKC, collapsed whitespace, look-alike letters folded,
  leetspeak and spaced letters joined, hidden tag text and base64 decoded.
- urgent() finds crisis, child-safety and secrecy-request messages in English, Hindi, Hinglish and algospeak and
  picks the reply language; the replies are fixed text, never model output.
- redact_personal_data() removes phone numbers (spaced, +91 or 0-prefixed), Aadhaar-like numbers, emails, passwords
  and "my address is ..." before storage or the model.
- promises_secrecy() catches a model reply that promises to keep a secret.
Patterns stay broad for crisis and abuse, where a miss is worst, and skip common idioms ("this sum is killing me",
"aaj test mein mar gaye", "ye question toh suicide hai").
"""
from __future__ import annotations

import base64
import binascii
import re
import unicodedata

from tutor.guards import RISK_PATTERN

# Invisible characters removed from every message. ZWNJ/ZWJ (U+200C/U+200D) are kept: Devanagari needs them.
_INVISIBLE = re.compile("[­​‎‏‪-‮⁠-⁤⁦-⁩﻿︀-︎"
                        "\U000e0000-\U000e007f\U000e0100-\U000e01ef]")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_JOINERS = re.compile("[‌‍]")
_CONFUSABLE = str.maketrans({"а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "ѕ": "s",
                             "ј": "j", "А": "A", "Е": "E", "О": "O", "Р": "P", "С": "C", "Х": "X", "І": "I", "Ѕ": "S",
                             "ԁ": "d", "ɡ": "g", "һ": "h", "ո": "n", "ս": "u"})
_LEET = str.maketrans({"4": "a", "3": "e", "1": "i", "0": "o", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i"})
_B64 = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/])")


def clean_text(text: str) -> str:
    """The message as stored and sent to the model: invisible and control characters removed, nothing else changed."""
    return _CONTROL.sub("", _INVISIBLE.sub("", text))


def screening_text(text: str) -> str:
    """A matching-only copy that undoes common disguises. Never shown, stored or sent to a model."""
    hidden = "".join(chr(ord(c) - 0xE0000) for c in text if 0xE0020 <= ord(c) <= 0xE007E)
    base = unicodedata.normalize("NFKC", _JOINERS.sub("", clean_text(text)))
    base = re.sub(r"\s+", " ", base).strip()
    variants = [base, base.translate(_CONFUSABLE)]
    folded = variants[-1]
    if any(re.search(r"[a-z]", w, re.I) and re.search(r"[0-9@$!]", w) for w in folded.split()):
        variants.append(folded.translate(_LEET))
    joined = re.sub(r"\b(\w) (?=\w\b)", r"\1", folded)            # "s u i c i d e" -> "suicide"
    if joined != folded:
        variants.append(joined)
    if hidden:
        variants.append(hidden)
    for token in _B64.findall(base):
        try:
            decoded = base64.b64decode(token + "=" * (-len(token) % 4), validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue
        if decoded and sum(ch.isprintable() for ch in decoded) / len(decoded) > 0.9:
            variants.append(decoded)
    return "\n".join(variants)


CRISIS = re.compile("|".join([
    RISK_PATTERN,
    r"\bk[i1!]l+(?:ing)? ?m[yi]s[e3]lf\b", r"\b(?:un-?alive|unaliv(?:e|ing)) (?:my ?self|me)\b|\bwant(?:na)? to unalive\b",
    r"\bkms\b", r"\bsewer ?slide\b", r"\bsuicidal\b",
    r"\b(?:commit|thinking (?:of|about)|thoughts? of|want(?:ed)? to|going to|plan(?:ning)? to|try(?:ing)? to)\b.{0,12}\bsu[i1!]c[i1!]de?\b",
    r"\bsu[i1!]c[i1!]de?\b.{0,12}\b(?:karna|kar lu|kar lunga|kar lungi|karne|note|letter|plan|thoughts?)\b",
    r"\bhow many (?:paracetamol|crocin|tablets|pills|sleeping pills)\b.{0,30}\b(?:too many|to die|not wake|overdose|kill)\b",
    r"\bhow many sleeping pills\b|\bhow many pills (?:would|should|does it|do i need|to)\b", r"\b(?:if i|when i|should i) jump (?:from|off)\b", r"\bjump (?:from|off) the \d+\w* floor\b",
    r"\bend(?:ing|ed)? (?:my (?:own )?life|it all)\b", r"\btried to (?:end|kill|take)\b",
    r"\b(?:want|wanna|going|planning|ready) to die\b(?! (?:laughing|of (?:laughter|boredom|embarrassment)))",
    r"\bbetter off (?:dead|without me)\b", r"\bhappier without me\b", r"\b(?:i'?m|i am) (?:just )?a burden\b",
    r"\bnobody would (?:notice|care|miss me)\b.{0,40}\b(?:disappear|gone|died?)\b|\bif i (?:just )?disappeared\b",
    r"\b(?:won'?t|will not) be (?:here|around|alive)\b", r"\bdon'?t want to (?:live|be alive|exist|wake up)\b",
    r"\bsleep and never wake up\b|\bnot wake up\b", r"\bwant it all to stop\b", r"\bdone with (?:life|living)\b",
    r"\bgiving (?:my )?(?:things|stuff|belongings) away\b", r"\bgoodbye (?:letter|note)\b",
    r"\bletters? to my (?:family|parents)\b.{0,60}\b(?:in case|tonight|happens to me)\b",
    r"\bjump (?:from|off) (?:the |a )?(?:terrace|roof|building|bridge|balcony)\b", r"\bcan'?t survive the fall\b",
    r"\bcutting (?:again|myself)\b|\b(?:cut|hurt|harm)(?:ting)? myself\b",
    r"\b(?:painless|easiest|quickest) way to die\b", r"\bwants? to kill (?:herself|himself|themselves)\b",
    r"\bif something happens to me\b",
    r"jee?ne ka (?:mann?|dil) nahi", r"jee?na nahi chaht", r"sab khatam kar (?:dena|dunga|doon|du|lunga)",
    r"\bbojh (?:hu|hoon|hun)\b", r"\b(?:ek )?burden (?:hu|hoon|hun|hai)\b", r"chhat se kood", r"neend ki goli",
    r"paida hi na hota", r"\bmar jaun toh\b", r"\bmujhe marna (?:hai|h)\b", r"ab aur nahi hota.{0,30}khatam",
    r"hamesha ke liye chal[ai] jaun|chal[ai] jaun hamesha ke liye", r"khud ko (?:khatam|maar)", r"\bphaa?nsi\b",
    r"zeh?e?r kha", r"blade (?:maara|se kaat)", r"\bmere jaane ke baad\b", r"\bghar wapas nahi jaunga\b.{0,20}\bkabhi nahi\b",
    r"जीने का मन नहीं", r"जीना नहीं चाहत", r"सब कुछ खत्म कर", r"बोझ हूँ", r"बोझ बन गय", r"मेरे बिना सब खुश",
    r"किसी को परेशान नहीं करूँगा", r"ब्लेड से काट", r"पंखे से लटक", r"फाँसी", r"फांसी", r"ज़हर खा", r"जहर खा",
    r"नींद की गोलि", r"मर ही जाऊँ", r"मर जाना चाहत",
    r"சாக விரும்ப", r"বাঁচতে চাই না",
]), re.I)
CHILD_SAFETY = re.compile("|".join([
    r"\btouch(?:es|ed|ing)? me\b.{0,60}\b(?:don'?t like|secret|wrong|uncomfortable)\b",
    r"\btouch\w* me\b.{0,30}\binappropriately\b|\binappropriately\b.{0,20}\btouch\w* me\b",
    r"galat (?:tarike|tareeke) se chh?[uo]", r"गलत तरीके से छू", r"\bcomes into my room at night\b",
    r"\b(?:send|sending) (?:me )?(?:pictures|pics|photos|nudes)\b.{0,80}\bsecret\b", r"\bkeep it secret from my parents\b",
    r"\bprivate (?:photos|pictures|pics)\b.{0,80}\b(?:post|share|leak|unless|viral)\b", r"\bphotos? morph",
    r"\bbeats? me\b|\bhits? me with\b|\bbelt se maar",
    r"\bmarried\b.{0,40}\bi'?m 1[0-7]\b|\bshaadi\b.{0,60}\b1[0-7] (?:ki|ka|saal)",
    r"\bmeet (?:me )?alone\b.{0,80}\b(?:not to tell|secret|don'?t tell)\b", r"\bwhat i'?m wearing\b",
    r"गंदी तस्वीरें", r"\bstay back alone\b", r"\bmere saath galat (?:kiya|kaam|harkat)", r"मेरे साथ गलत",
    r"\bdoes (?:stuff|things) to me\b", r"\bdelete our chats\b", r"\bhamara raaz\b|हमारा राज़",
]), re.I)
SECRECY = re.compile("|".join([
    r"\b(?:promise|swear)\b.{0,40}\b(?:won'?t|will not|not to|don'?t|never)\s+tell\b",
    r"\b(?:don'?t|do not|never)\s+tell anyone\b.{0,60}\bpromise\b", r"\bpromise (?:first|me)\b.{0,60}\btell you\b",
    r"\bcan you keep a secret\b", r"\bkisi ko (?:mat )?bata(?:na|oge|nge)\b.{0,40}\bpromise\b", r"\bpromise karo\b",
    r"किसी को मत बताना.{0,40}वादा|वादा करो",
]), re.I)
_HINGLISH = re.compile(r"\b(?:hai|hain|nahi|nhi|kya|karo|karun|mujhe|mujhse|yaar|hoon|hu|kaise|kyun|bata|samjha|samajh|"
                       r"mein|toh|bhai|aap|tum|kar|ho|wale|wala|ke|ki|ka|se|hota|hoti|raha|rahi|bas|ab|aur|koi|kuch)\b", re.I)


def guess_language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if letters and sum("ऀ" <= c <= "ॿ" for c in letters) / len(letters) > 0.3:
        return "hi"
    return "hinglish" if len(_HINGLISH.findall(text)) >= 2 else "en"


REPLIES = {
    "crisis": {
        "en": "I'm really glad you told me, and I'm sorry it feels this heavy. Your safety matters most. Please talk to a trusted "
              "adult near you right now. You can call Tele-MANAS, India's free 24x7 mental health helpline, on 14416 or "
              "1-800-891-4416. If you are in immediate danger, call 112. Can you reach someone who can stay with you?",
        "hi": "आपने बताया, यह अच्छा किया, और मुझे दुख है कि यह इतना भारी लग रहा है। आपकी सुरक्षा सबसे ज़रूरी है। अभी किसी भरोसेमंद "
              "बड़े से बात करें। Tele-MANAS हेल्पलाइन 14416 या 1-800-891-4416 (मुफ़्त, 24x7, हिंदी में भी) पर कॉल करें। ख़तरा हो तो "
              "112 पर कॉल करें। आप अकेले नहीं हैं। क्या कोई आपके पास रह सकता है?",
        "hinglish": "Aapne bataya, yeh achha kiya. Mujhe dukh hai ki yeh itna bhaari lag raha hai. Aapki safety sabse zaroori hai. "
                    "Abhi kisi bharosemand bade se baat karo. Tele-MANAS helpline 14416 ya 1-800-891-4416 (free, 24x7, Hindi mein "
                    "bhi) par call karo. Khatra ho toh 112 par call karo. Aap akele nahi ho. Kya koi aapke paas reh sakta hai?",
    },
    "child_safety": {
        "en": "Thank you for telling me. This is not your fault, and you don't have to keep it a secret. Please tell a trusted adult "
              "today, like a parent, teacher or school counsellor. You can call Childline on 1098 (free, 24x7). For online threats "
              "or photos, you can also call 1930. If you are in danger now, call 112. Is there an adult you trust you can tell today?",
        "hi": "मुझे बताने के लिए धन्यवाद। इसमें आपकी कोई गलती नहीं है, और आपको इसे राज़ रखने की ज़रूरत नहीं है। आज ही किसी भरोसेमंद बड़े "
              "को बताएँ, जैसे माता-पिता, शिक्षक या स्कूल काउंसलर। चाइल्डलाइन 1098 (मुफ़्त, 24x7) पर कॉल करें। ऑनलाइन धमकी या फ़ोटो के लिए "
              "1930 पर भी कॉल कर सकते हैं। ख़तरा हो तो 112 पर कॉल करें। क्या कोई भरोसेमंद बड़ा है जिसे आप आज बता सकें?",
        "hinglish": "Mujhe batane ke liye thank you. Isme aapki koi galti nahi hai, aur aapko ise secret rakhne ki zaroorat nahi hai. "
                    "Aaj hi kisi bharosemand bade ko batao, jaise mummy-papa, teacher ya school counsellor. Childline 1098 (free, 24x7) "
                    "par call karo. Online dhamki ya photos ke liye 1930 par bhi call kar sakte ho. Khatra ho toh 112 par call karo. "
                    "Kya koi bada hai jise aap aaj bata sako?",
    },
    "secrecy": {
        "en": "I'm glad you want to share, and I'm listening. I can't promise to keep a secret if someone's safety is involved, "
              "because the safest step is to tell a trusted adult who can help. You can also call Childline on 1098 (free, 24x7). "
              "What would you like to tell me?",
        "hi": "आप बताना चाहते हैं, यह अच्छा है, मैं सुन रहा हूँ। अगर किसी की सुरक्षा की बात हो तो मैं राज़ रखने का वादा नहीं कर सकता, "
              "क्योंकि सबसे सुरक्षित कदम किसी भरोसेमंद बड़े को बताना है। आप चाइल्डलाइन 1098 (मुफ़्त, 24x7) पर भी कॉल कर सकते हैं। "
              "आप क्या बताना चाहेंगे?",
        "hinglish": "Aap batana chahte ho, yeh achha hai, main sun raha hoon. Agar kisi ki safety ki baat ho toh main secret rakhne ka "
                    "promise nahi kar sakta, kyunki sabse safe step kisi bharosemand bade ko batana hai. Aap Childline 1098 (free, "
                    "24x7) par bhi call kar sakte ho. Aap kya batana chahoge?",
    },
}


# Everyday exaggeration removed before matching, so the older shared pattern (bare "suicide", "want to die")
# does not fire on it: "die laughing", "dying of boredom", "this question is suicide" (Hinglish slang for very hard).
_IDIOMS = re.compile(r"(?i)\b(?:want|wanna|going) to die (?:laughing|of (?:laughter|boredom|embarrassment))\b|"
                     r"\b(?:question|sawal|sawaal|sum|paper|chapter|test|exam)\s+(?:toh |to |is |hai )?(?:pura |ekdum )?suicide\b")


def urgent(text: str):
    """Return (kind, language) for a crisis, child-safety or secrecy-request message, else None."""
    screen = _IDIOMS.sub(" ", screening_text(text))
    for kind, pattern in (("crisis", CRISIS), ("child_safety", CHILD_SAFETY), ("secrecy", SECRECY)):
        if pattern.search(screen):
            return kind, guess_language(text)
    return None


def reply_for(kind: str, language: str) -> str:
    table = REPLIES[kind]
    return table.get(language, table["en"])


class UrgentScreen:
    """Drop-in for the old DISTRESS regex: .search(text) is truthy for any message that gets a fixed safety reply."""

    def search(self, text):
        return urgent(text)


_PII = [
    (re.compile(r"(?<![\w@])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I), "[email removed]"),
    (re.compile(r"(?<!\d)[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"), "[ID number removed]"),
    (re.compile(r"(?<![\d.])(?:\+?91[\s-]?|0)?[6-9]\d{4}[\s-]?\d{5}(?![\d.])"), "[phone removed]"),
    (re.compile(r"(?i)\b(password|passcode|pwd)\s*(?:is|:|=|hai)\s*\S+"), r"\1 [removed]"),
    (re.compile(r"(?i)\b(?:my (?:home )?address is|i live at|ghar ka pata)\b[^.?!\n]{0,90}"), "[address removed]"),
]


def redact_personal_data(text: str) -> str:
    for pattern, replacement in _PII:
        text = pattern.sub(replacement, text)
    return text


_SECRET_PROMISE = re.compile(r"(?i)\b(?:i|we)\s+(?:promise|swear|will|won'?t)\b[^.?!]{0,40}\b(?:won'?t|not|never)?\s*tell (?:anyone|anybody)\b|"
                             r"\bi(?:'ll| will| can| promise to)?\s+keep (?:it|this|that|your secret)(?: a)? secret\b|\byour secret is safe\b|"
                             r"\bkisi ko nahi bata(?:unga|ungi|yenge)\b|किसी को नहीं बताऊँगा")


def promises_secrecy(reply: str) -> bool:
    return bool(_SECRET_PROMISE.search(reply or ""))
