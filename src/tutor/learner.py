"""Learner model maths and study planning. Code decides; a model may only word the plan."""
from __future__ import annotations

from .config import SETTINGS
from .setup_content import load

LM = SETTINGS.learner_model
GUESS_BY_KIND = {"finite_set": 0.05, "scalar": 0.05, "boolean": 0.5}


def bkt_update(p: float, correct: bool, guess: float | None = None) -> float:
    """Bayesian Knowledge Tracing: observation update, then the learning step."""
    s, t = LM["p_slip"], LM["p_learn"]
    g = LM["p_guess_set"] if guess is None else guess
    if correct:
        post = p * (1 - s) / (p * (1 - s) + (1 - p) * g)
    else:
        post = p * s / (p * s + (1 - p) * (1 - g))
    return round(post + (1 - post) * t, 4)


def concept_graph() -> dict[str, dict]:
    return {c["concept_id"]: c for c in load("concepts")}


def make_plan(snapshot: dict, previous: dict | None = None, reason: str | None = None) -> dict:
    """Outer fringe of the prerequisite graph: unmastered concepts whose prerequisites are ready."""
    graph = concept_graph()
    mastery = {cid: snapshot["mastery"].get(cid, LM["p_init"]) for cid in graph}
    active_mis = {m: v for m, v in snapshot.get("misconceptions", {}).items() if v["status"] in ("suspected", "confirmed")}
    mis_concepts = {m["misconception_id"]: m["concept_id"] for m in load("misconceptions")}
    flagged = {mis_concepts[m] for m in active_mis if m in mis_concepts}

    def unlocks(cid: str) -> int:
        return sum(1 for c in graph.values() if cid in c["prerequisites"])

    fringe = [cid for cid, c in graph.items() if mastery[cid] < LM["mastered"]
              and all(mastery[p] >= LM["prerequisite_ready"] for p in c["prerequisites"])]
    # Flagged concepts come first even if a prerequisite is weak: fix the misconception, then move on.
    candidates = sorted(set(fringe) | flagged, key=lambda cid: (cid not in flagged, -unlocks(cid), mastery[cid]))
    steps = []
    for cid in candidates[:3]:
        weak = [p for p in graph[cid]["prerequisites"] if mastery[p] < LM["prerequisite_ready"]]
        action = "review_prerequisite" if weak else ("remediate" if cid in flagged else "practise")
        steps.append({"concept_id": cid, "title": graph[cid]["title"], "action": action,
                      "mastery": round(mastery[cid], 2),
                      "why": ("misconception flagged" if cid in flagged else "next ready concept")
                      + (f"; weak prerequisite {', '.join(weak)}" if weak else "")})
    version = (previous or {}).get("version", 0) + 1
    return {"version": version, "steps": steps, "replan_reason": reason,
            "mastered": sorted(cid for cid in graph if mastery[cid] >= LM["mastered"])}


def make_topic_plan(snapshot: dict, chapter: str, results: list[dict], previous: dict | None = None) -> dict:
    """Prioritise concepts associated with incorrect quiz responses, without inferring a cause."""
    from .topic_sources import concepts
    graph = {c['concept_id']: c for c in concepts() if c.get('chapter') == chapter}
    evidence = {}
    for result in results:
        for cid in result['concept_ids']:
            if cid not in graph:
                continue
            entry = evidence.setdefault(cid, {'attempts': 0, 'incorrect': 0, 'question_ids': []})
            entry['attempts'] += 1
            entry['incorrect'] += int(not result['correct'])
            entry['question_ids'].append(result['question_id'])
    order = sorted(evidence, key=lambda cid: (-evidence[cid]['incorrect'],
                                               snapshot['mastery'].get(cid, LM['p_init']), cid))
    steps = []
    for cid in order[:3]:
        e = evidence[cid]
        why = f"{e['incorrect']} of {e['attempts']} associated quiz answers incorrect"
        steps.append({'concept_id': cid, 'title': graph[cid]['title'],
                      'action': 'review' if e['incorrect'] else 'practise',
                      'mastery': round(snapshot['mastery'].get(cid, LM['p_init']), 2),
                      'why': why, 'evidence_question_ids': e['question_ids']})
    score = sum(item['correct'] for item in results)
    return {'chapter': chapter, 'version': (previous or {}).get('version', 0) + 1,
            'steps': steps, 'replan_reason': f"after quiz: scored {score}/{len(results)}",
            'mastered': []}
