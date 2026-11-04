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


def _quiz_evidence(results: list[dict], graph: dict) -> dict:
    evidence = {}
    for result in results:
        if not result.get("scorable", True):
            continue
        for cid in result["concept_ids"]:
            if cid not in graph:
                continue
            entry = evidence.setdefault(cid, {"attempts": 0, "incorrect": 0, "question_ids": []})
            entry["attempts"] += 1
            entry["incorrect"] += int(not result["correct"])
            entry["question_ids"].append(result["question_id"])
    return evidence


def make_plan(snapshot: dict, previous: dict | None = None, reason: str | None = None,
              quiz_results: list[dict] | None = None) -> dict:
    """Outer fringe of the prerequisite graph: unmastered concepts whose prerequisites are ready."""
    graph = concept_graph()
    mastery = {cid: snapshot["mastery"].get(cid, LM["p_init"]) for cid in graph}
    active_mis = {m: v for m, v in snapshot.get("misconceptions", {}).items() if v["status"] in ("suspected", "confirmed")}
    mis_concepts = {m["misconception_id"]: m["concept_id"] for m in load("misconceptions")}
    flagged = {mis_concepts[m] for m in active_mis if m in mis_concepts}

    evidence = _quiz_evidence(quiz_results or [], graph)
    missed = {cid for cid, e in evidence.items() if e["incorrect"]}
    passed = {cid for cid, e in evidence.items() if not e["incorrect"]} - flagged

    def unlocks(cid: str) -> int:
        return sum(1 for c in graph.values() if cid in c["prerequisites"])

    fringe = [cid for cid, c in graph.items() if mastery[cid] < LM["mastered"] and cid not in passed
              and all(mastery[p] >= LM["prerequisite_ready"] or p in passed for p in c["prerequisites"])]
    # Quiz mistakes take priority, including when a prerequisite still needs review.
    candidates = sorted(set(fringe) | flagged | missed,
                        key=lambda cid: (cid not in missed, cid not in flagged,
                                         not any(p in passed for p in graph[cid]["prerequisites"]),
                                         -unlocks(cid), mastery[cid], cid))
    steps = []
    for cid in candidates[:3]:
        weak = [p for p in graph[cid]["prerequisites"] if mastery[p] < LM["prerequisite_ready"] and p not in passed]
        action = "review_prerequisite" if weak else ("remediate" if cid in flagged or cid in missed else "practise")
        why = (f"{evidence[cid]['incorrect']} of {evidence[cid]['attempts']} associated quiz answers incorrect"
               if cid in missed else "misconception flagged" if cid in flagged else "next ready concept")
        step = {"concept_id": cid, "title": graph[cid]["title"], "action": action,
                "mastery": round(mastery[cid], 2),
                "why": why + (f"; weak prerequisite {', '.join(weak)}" if weak else "")}
        if cid in evidence:
            step["evidence_question_ids"] = evidence[cid]["question_ids"]
        steps.append(step)
    version = (previous or {}).get("version", 0) + 1
    return {"version": version, "steps": steps, "replan_reason": reason,
            "mastered": sorted(cid for cid in graph if mastery[cid] >= LM["mastered"]),
            "quiz_passed": sorted(passed)}


def make_topic_plan(snapshot: dict, chapter: str, results: list[dict], previous: dict | None = None) -> dict:
    """Review quiz mistakes, then select ready successors; successful associations are not mastery."""
    from .topic_sources import concepts
    graph = {c['concept_id']: c for c in concepts() if c.get('chapter') == chapter}
    evidence = _quiz_evidence(results, graph)
    mastery = {cid: snapshot['mastery'].get(cid, LM['p_init']) for cid in graph}
    missed = {cid for cid, e in evidence.items() if e['incorrect']}
    passed = set(evidence) - missed
    ready = {cid for cid, c in graph.items() if cid not in passed and mastery[cid] < LM['mastered']
             and all(mastery.get(p, LM['p_init']) >= LM['prerequisite_ready'] or p in passed
                     for p in c['prerequisites'])}
    order = sorted(missed | ready, key=lambda cid: (cid not in missed,
                   -evidence.get(cid, {}).get('incorrect', 0),
                   not any(p in passed for p in graph[cid]['prerequisites']), mastery[cid], cid))
    steps = []
    for cid in order[:3]:
        e = evidence.get(cid)
        weak = [p for p in graph[cid]['prerequisites']
                if mastery.get(p, LM['p_init']) < LM['prerequisite_ready'] and p not in passed]
        why = (f"{e['incorrect']} of {e['attempts']} associated quiz answers incorrect" if cid in missed
               else "next ready concept after quiz")
        if weak:
            why += f"; review prerequisite {', '.join(weak)}"
        steps.append({'concept_id': cid, 'title': graph[cid]['title'],
                      'action': 'review' if cid in missed else 'practise',
                      'mastery': round(mastery[cid], 2), 'why': why,
                      'evidence_question_ids': e['question_ids'] if e else []})
    score = sum(item['correct'] for item in results)
    return {'chapter': chapter, 'version': (previous or {}).get('version', 0) + 1,
            'steps': steps, 'replan_reason': f"after quiz: scored {score}/{len(results)}",
            'mastered': sorted(cid for cid in graph if mastery[cid] >= LM['mastered']),
            'quiz_passed': sorted(passed)}
