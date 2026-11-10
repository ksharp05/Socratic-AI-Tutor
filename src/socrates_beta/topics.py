"""Topic navigation derived from the active, scoped knowledge catalogue."""
import re
from ncert_pipeline.retrieval import query_terms

CHAPTERS = {
 4:("Quadratic Equations",r"\bquadratic(?: equations?)?\b"),
 5:("Arithmetic Progressions",r"\barithmetic progressions?\b|\ba\.?p\.?\b"),
 8:("Introduction to Trigonometry",r"\btrig(?:onometry|onometric)?\b"),
}
OPENING_WORDS=set("trig trigonometry trigonometric quadratic equation equations arithmetic progression progressions ap introduction intro basics basic start starting learn learning overview chapter topic lesson teach teaching tell introduction begin beginning introduction some give".split())

def broad_topic(adapter,query,scope):
    if scope.grade!=10 or scope.subject.casefold()!="mathematics":return None
    matches=[unit for unit,(_,pattern) in CHAPTERS.items() if re.search(pattern,query,re.I)]
    if len(matches)!=1:return None
    unit=matches[0]
    if scope.unit is not None and scope.unit!=unit:return None
    terms=set(getattr(adapter,"terms",query_terms)(query))
    if terms-OPENING_WORDS:return None
    nodes=[n for n in adapter.nodes(scope) if n.get("unit_file_index")==unit and n.get("kind")=="concept"]
    # Use catalogue prerequisites to start with the foundation, not a rare formula.
    nodes.sort(key=lambda n:(len(n.get("prerequisites",[])),n["id"]))
    return nodes or None

def discovery_question(message):
    return bool(re.search(r"\b(?:what|which)\s+(?:other\s+)?(?:topics?|subjects?|chapters?)\b|"
                          r"\bwhat\s+can\s+you\s+(?:teach|help|cover)\b|"
                          r"\b(?:list|show)\s+(?:me\s+)?(?:the\s+)?(?:available\s+)?(?:topics?|subjects?|chapters?)\b",
                          message,re.I))

def topic_labels(adapter,scope):
    nodes=adapter.nodes(scope)
    units={n.get("unit_file_index") for n in nodes}
    if scope.grade==10 and scope.subject.casefold()=="mathematics":
        labels=[name for unit,(name,_) in CHAPTERS.items() if unit in units]
        if labels:return labels
    return list(dict.fromkeys(n["title"] for n in nodes))[:4]

def navigation_reply(adapter,scope,*,missing=False,language='en'):
    labels=topic_labels(adapter,scope)
    if not labels:
        return "There are no reading topics in this selection yet. Could you choose an available class and subject in Explore?"
    listing=", ".join(labels[:-1])+" and "+labels[-1] if len(labels)>1 else labels[0]
    if missing and language=='hi':
        return ("अच्छा सवाल है, पर यह मुझे इस चयन के स्रोतों में नहीं मिला, इसलिए मैं अनुमान नहीं लगाऊँगा। आपके शिक्षक या पाठ्यपुस्तक मदद कर "
                "सकते हैं। यहाँ मैं इनमें मदद कर सकता हूँ: "+listing+"। आप किससे शुरू करना चाहेंगे?")
    if missing and language=='hinglish':
        return ("Achha sawaal hai, par yeh mujhe is selection ke sources mein nahi mila, isliye main guess nahi karunga. Aapke teacher "
                "ya textbook help kar sakte hain. Yahan main in topics mein help kar sakta hoon: "+listing+". Kahan se shuru karein?")
    prefix=("That's a good question, but I can't find it in my sources for this selection, so I won't guess. Your teacher or "
            "textbook can help with it. ") if missing else ""
    return prefix+"In this selection I can help with "+listing+". Which would you like to start with?"
