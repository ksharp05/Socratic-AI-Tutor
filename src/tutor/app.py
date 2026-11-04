"""The tutor: a LangGraph session graph (supervisor/planner + four specialists) and a teacher-approval graph.

Request path (see Docs/plan/04-architecture.md): input guard -> load learner -> planner -> one specialist
-> output guard (one self-correction retry) -> update memory -> respond. All tool calls go through the ToolBus.
"""
from __future__ import annotations

import hashlib
import json
import operator
import re
import sqlite3
import uuid
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from filelock import Timeout
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from . import approval_token, guards, learner, prompts, store
from .config import SETTINGS, db_path
from .llm import LLM
from .question_catalog import allowed
from .topic_sources import cards as topic_cards, concepts as topic_concepts, CHAPTERS
from .setup_content import load
from .toolbus import CallContext, ToolBus, ToolCallError

MIS_KEYWORDS = {
    "qe_m01": [r"\bx\s*(\^|squared|²)\b.*\bquadratic\b", r"\bany equation\b.*\bquadratic\b"],
    "qe_m02": [r"\bcoefficient\b", r"\bsign\b.*\b(b|c)\b"],
    "qe_m03": [r"\ba\s*=\s*0\b", r"\ba is (zero|0)\b"],
    "qe_m04": [r"\bdivid\w*\b.*\bby x\b", r"\bcancel\w*\b.*\bx\b", r"\bonly one (root|factor|answer)\b",
               r"\bdivided both sides\b"],
    "qe_m05": [r"\bsquare root\b", r"√", r"\bsqrt\b", r"\bonly (the )?positive\b"],
    "qe_m06": [r"±", r"\bplus[- ]minus\b"],
}
PRACTICE_REQUEST = re.compile(r"^/practice\b|\b(practice|another (one|question)|next question|give me a (question|problem))\b", re.I)
QUIZ_REQUEST = re.compile(r"^/quiz\b|\b(start|take) (a |the )?quiz\b", re.I)
HINT_REQUEST = re.compile(r"\b(hint|help|stuck|don'?t know|idk|no idea)\b", re.I)
ANSWER_LIKE = re.compile(r"(\b[a-z]\s*=\s*[-+]?\s*[\d(√s])|^[\s{(]*(?:(?:(?:my|the) answer is|i think (?:the answer is|it(?:'s| is))|it(?:'s| is))\s*[:=]?\s*)?[-+]?\s*(?:[\d√]|sqrt\s*\()|\bno real roots?\b", re.I)
STUCK_SIGNAL = re.compile(r"\b(stuck|no idea|don'?t know|idk)\b", re.I)
GUESS_BY_KIND = learner.GUESS_BY_KIND


class TutorState(TypedDict, total=False):
    messages: Annotated[list[dict], operator.add]
    incoming: str
    screen: dict
    unverified_own_problem: bool
    question_revoked: bool
    session: dict
    learner: dict
    plan: dict
    active_item: dict | None
    attempted: list[str]
    focus_misconception: str | None
    probe_asked_for: str | None
    hint_stage: int
    diagnosis: dict | None
    route: str
    draft: dict | None
    checks: dict
    revision_count: int
    grade: dict | None
    quiz: dict | None
    retrieved: list[dict]
    notes: list[str]
    resolve_progress: dict


class ApprovalState(TypedDict, total=False):
    set_id: str
    concept_id: str
    mode: str
    thread_id: str
    edit_question_ids: list[str] | None
    payload_sha256: str
    decision: dict | None
    status: str
    token: str | None
    message: str


class TutorApp:
    def __init__(self, *, defences: bool = True, llm_mode: str | None = None, extra_items: list[dict] | None = None,
                 db_name: str = "tutor.db", checkpoint_name: str = "checkpoints.db",
                 allow_dev_fixtures: bool = False):
        self.conn = store.connect(db_path(db_name))
        self.bus = ToolBus(self.conn, extra_items, allow_dev_fixtures=allow_dev_fixtures)
        self.llm = LLM(self.conn, llm_mode)
        self.defences = defences
        self.misconceptions = {m["misconception_id"]: m for m in load("misconceptions")}
        self.cards = {c["passage_id"]: c for c in topic_cards()}
        self.concepts = {c["concept_id"]: c for c in topic_concepts()}
        self._ctx: dict[str, CallContext] = {}
        self.checkpointer = SqliteSaver(sqlite3.connect(db_path(checkpoint_name), check_same_thread=False))
        self.graph = self._build_session_graph().compile(checkpointer=self.checkpointer)
        self.approval = self._build_approval_graph().compile(checkpointer=self.checkpointer)

    # ------------------------------------------------------------------ helpers
    def _ctx_for(self, state: dict, node: str) -> CallContext:
        session = state["session"]
        ctx = self._ctx.setdefault(session["session_id"], CallContext(
            session_id=session["session_id"], learner_id=session.get("learner_id"),
            budget=SETTINGS.budgets["tool_calls_per_session"]))
        ctx.node = node
        return ctx

    def _call(self, state: dict, node: str, role: str, server: str, tool: str, args: dict) -> dict:
        return self.bus.call(self._ctx_for(state, node), role, server, tool, args)

    def _note(self, state: dict, node: str, decision: str, detail: dict | None = None) -> None:
        store.trace(self.conn, session_id=state["session"]["session_id"], node=node, role="graph", kind="decision",
                    name=decision, detail=detail)

    def _keyword_candidates(self, text: str) -> list[str]:
        scored = []
        for mid, patterns in MIS_KEYWORDS.items():
            hits = sum(1 for p in patterns if re.search(p, text, re.I))
            if hits and mid in self.misconceptions:
                scored.append((hits, mid))
        return [mid for _, mid in sorted(scored, reverse=True)]

    def _best_style(self, snapshot: dict, mid: str) -> str | None:
        rows = [s for s in snapshot.get("styles", []) if s["misconception_id"] == mid and s["successes"] > s["failures"]]
        return max(rows, key=lambda s: s["successes"])["style"] if rows else None

    def _publication_unavailable(self, state: TutorState, *, include_completed: bool = False) -> bool:
        """Fail closed if a referenced question no longer has its approved version."""
        referenced = []
        if state.get("active_item"):
            referenced.append((state["active_item"], "practice"))
        quiz = state.get("quiz") or {}
        items = quiz.get("items", [])
        referenced.extend((item, "quiz") for item in (items if include_completed else items[quiz.get("index", 0):]))
        if include_completed and state.get("grade"):
            referenced.append((state["grade"], "practice"))
        if not referenced:
            return False
        try:
            visible = self._call(state, "input_guard", "question_setter", "question-bank", "list_published", {})["items"]
            valid = {(i["question_id"], i["set_id"], i["set_payload_sha256"], mode)
                     for i in visible for mode in ("practice", "quiz") if allowed(i, mode)}
            revoked = any((i.get("question_id"), i.get("set_id"), i.get("set_payload_sha256"), mode) not in valid
                          for i, mode in referenced)
        except Exception as exc:
            revoked = True
            self._note(state, "input_guard", "publication_check_failed", {"error_type": type(exc).__name__})
        if revoked:
            self._note(state, "input_guard", "question_publication_unavailable")
        return revoked

    # ------------------------------------------------------------------ session graph nodes
    def _input_guard(self, state: TutorState) -> dict:
        screen = state.get("screen") or {}
        notes = []
        if screen.get("pii_redacted"):
            notes.append("Personal details were removed from your message before anything stored or processed it.")
        if screen.get("injection"):
            notes.append("I ignored instructions inside the text you pasted; I only treat it as maths to discuss.")
        # The existing checker can protect registered practice items, but does not
        # have a verified key for arbitrary learner-supplied homework. Keep that
        # distinction across follow-ups until a new registered practice/quiz starts.
        own_problem = bool(state.get("unverified_own_problem"))
        if self.defences and "unverified_own_problem" not in state and not state.get("active_item") and not state.get("quiz"):
            # Older persisted sessions predate this field; recover the boundary
            # from their already-redacted student messages before any model call.
            own_problem = any(guards.unverified_own_problem(m.get("content", ""))
                              for m in state.get("messages", []) if m.get("role") == "student")
        if self.defences and not state.get("quiz") and screen.get("unverified_own_problem"):
            # A plain numeric assignment while a registered item is active is an
            # answer attempt; an additional equation is still unverified homework.
            simple_answer = bool(state.get("active_item") and re.fullmatch(
                r"\s*[a-z]\s*=\s*[-+]?\s*\d+(?:\s*/\s*\d+)?\s*", state["incoming"], re.I))
            own_problem = own_problem or not simple_answer
        if PRACTICE_REQUEST.search(state["incoming"]) or QUIZ_REQUEST.search(state["incoming"]) or state["session"].get("mode") == "quiz":
            own_problem = False
        revoked = self._publication_unavailable(state)
        self._note(state, "input_guard", "screened", {k: v for k, v in screen.items() if k != "text"})
        if own_problem:
            self._note(state, "input_guard", "unverified_problem_deterministic_only")
            if self.llm.enabled:
                notes.append("For this unverified problem I can offer general guidance; automatic answer checking is not available here.")
        return {"messages": [{"role": "student", "content": state["incoming"]}], "incoming": "",
                "draft": None, "checks": {}, "revision_count": 0, "grade": None, "retrieved": [], "notes": notes,
                "diagnosis": None, "unverified_own_problem": own_problem, "question_revoked": revoked}

    def _load_learner(self, state: TutorState) -> dict:
        lid = state["session"]["learner_id"]
        snapshot = self._call(state, "load_learner", "study_planner", "learner-store", "read_learner", {"learner_id": lid})
        update: dict[str, Any] = {"learner": snapshot}
        if state["session"].get("chapter", "quadratic_equations") != "quadratic_equations":
            update["plan"] = snapshot.get("topic_plans", {}).get(state["session"]["chapter"])
            return update
        if not snapshot.get("plan"):
            plan = learner.make_plan(snapshot, reason="first plan")
            self._call(state, "load_learner", "study_planner", "learner-store", "save_plan", {"learner_id": lid, "plan": plan})
            update["plan"] = plan
        else:
            update["plan"] = snapshot["plan"]
        return update

    def _planner(self, state: TutorState) -> dict:
        text = state["messages"][-1]["content"]
        screen = state.get("screen") or {}
        mode = state["session"].get("mode", "practice")
        item, quiz = state.get("active_item"), state.get("quiz")
        if screen.get("distress"):
            route = "handoff"
        elif screen.get("role_claim") or screen.get("key_request"):
            route = "refuse"
        elif state.get("question_revoked"):
            route = "question_revoked"
        elif quiz and quiz.get("index", 0) < len(quiz.get("items", [])):
            route = "quiz_answer"
        elif QUIZ_REQUEST.search(text) or (mode == "quiz" and not quiz):
            route = "quiz_start"
        elif PRACTICE_REQUEST.search(text):
            route = "set_question"
        elif item and HINT_REQUEST.search(text):
            route = "tutor"
        elif item and ANSWER_LIKE.search(text.strip()):
            route = "grade"
        else:
            snapshot = state["learner"]
            candidates = (self._keyword_candidates(text)
                          if state["session"].get("chapter", "quadratic_equations") == "quadratic_equations" else [])
            flagged = [m for m, v in snapshot["misconceptions"].items() if v["status"] in ("suspected", "confirmed", "addressed")]
            cand = candidates[0] if candidates else None
            concept = self.misconceptions[cand]["concept_id"] if cand else None
            mastered = concept and snapshot["mastery"].get(concept, 0) >= SETTINGS.learner_model["mastered"]
            if cand and mastered and cand not in flagged:
                route = "tutor_extension"
            elif cand and state.get("probe_asked_for") != cand:
                route = "diagnose"
            else:
                route = "tutor"
            self._note(state, "planner", "candidates", {"keyword": candidates, "flagged": flagged, "mastered": bool(mastered)})
            if cand:
                self._note(state, "planner", "route", {"route": route, "misconception": cand})
                return {"route": route, "focus_misconception": cand}
        self._note(state, "planner", "route", {"route": route})
        return {"route": route}

    def _diagnose(self, state: TutorState) -> dict:
        mid = state["focus_misconception"]
        mis = self.misconceptions[mid]
        evidence = ["keywords in the student's message"]
        if self.llm.enabled and not state.get("unverified_own_problem"):
            catalogue = "\n".join(f"{m}: {v['incorrect_rule']}" for m, v in self.misconceptions.items())
            system, user = prompts.render(prompts.DIAGNOSTICIAN, catalogue=catalogue, message=state["messages"][-1]["content"])
            raw = self.llm.complete(session_id=state["session"]["session_id"], node="diagnose", role="diagnostician",
                                    system=system, user=user)
            try:
                verdict = json.loads(re.search(r"\{.*\}", raw or "", re.S).group(0))
                if verdict.get("misconception_id") in self.misconceptions:
                    mid, mis = verdict["misconception_id"], self.misconceptions[verdict["misconception_id"]]
                    evidence.append(f"LLM: {verdict.get('evidence', '')}"[:120])
            except Exception:
                pass
        self._call(state, "diagnose", "diagnostician", "learner-store", "read_learner",
                   {"learner_id": state["session"]["learner_id"]})
        flagged = state["learner"]["misconceptions"].get(mid)
        opener = ("We've seen this idea trip you up before, so let's check it carefully. " if flagged
                  else "Good question, let's check one thing first. ")
        text = f"{opener}{mis['diagnostic_probe']}"
        diagnosis = {"misconception_id": mid, "status": "confirmed" if flagged else "suspected", "evidence": evidence}
        return {"draft": {"text": text, "citations": [], "kind": "probe", "misconception_id": mid},
                "diagnosis": diagnosis, "focus_misconception": mid, "probe_asked_for": mid, "hint_stage": 0}

    def _passages_for(self, state: TutorState, node: str, query: str) -> list[dict]:
        found = self._call(state, node, "tutor", "textbook-kb", "search", {"query": query, "k": 2,
                                                                           "chapter": state["session"].get("chapter", "quadratic_equations")})["results"]
        return found

    def _tutor(self, state: TutorState, extension: bool = False) -> dict:
        snapshot, item = state["learner"], state.get("active_item")
        mid = state.get("focus_misconception")
        strict = state.get("revision_count", 0) > 0
        stage = state.get("hint_stage", 0)
        if state.get("unverified_own_problem") and not item:
            # Never return a whole retrieved passage or model-generated solution for
            # an unverified learner problem. A generic question does not expose a key.
            query = (self.concepts[self.misconceptions[mid]["concept_id"]]["title"]
                     if mid else state["messages"][-1]["content"])
            passages = self._passages_for(state, "tutor", query)
            cite = f" [{passages[0]['passage_id']}]" if passages else ""
            text = f"What first step could you try, and what assumption would it require?{cite}"
            style = "unverified_problem_fallback"
        elif item and not extension:
            passages = []
            for pid in item.get("supporting_passage_ids", [])[:1]:
                passages.append(self._call(state, "tutor", "tutor", "textbook-kb", "get_section", {"passage_id": pid}))
            stages = item["hint_stages"]
            hint = stages[min(item.get("hint_stage", 0), len(stages) - 1)]["prompt"]
            item = {**item, "hint_stage": min(item.get("hint_stage", 0) + 1, len(stages) - 1)}
            cite = f" [{passages[0]['passage_id']}]" if passages else ""
            text, style = f"Hint: {hint}{cite}", "item_hint"
        elif extension and mid:
            concept = self.misconceptions[mid]["concept_id"]
            passages = self._passages_for(state, "tutor", self.concepts[concept]["title"])
            cite = f" [{passages[0]['passage_id']}]" if passages else ""
            text = (f"You already know this topic well, so here's a quick check rather than a long explanation: "
                    f"{self.concepts[concept]['diagnostic_probe']}{cite} Once you've checked that, try a harder one "
                    f"by typing 'practice'.")
            style = "extension"
        elif mid:
            mis = self.misconceptions[mid]
            concept = self.concepts[mis["concept_id"]]
            passages = self._passages_for(state, "tutor", f"{concept['title']} {mis['correct_reasoning']}")
            cite = f" [{passages[0]['passage_id']}]" if passages else ""
            style = self._best_style(snapshot, mid) or ("socratic_question" if stage == 0 else "counterexample")
            ladder = mis["hint_ladder"]
            step = ladder[min(stage, len(ladder) - 1)]
            if style == "counterexample" and not strict:
                text = f"{step} Try a value that makes one factor zero and check the original equation.{cite} What do you notice?"
            else:
                text = f"{step} {concept['hint']}{cite} What would you check next?"
            if self.llm.enabled and not strict and not state.get("unverified_own_problem"):
                passages_txt = "\n".join(f"[{p['passage_id']}] {p['text']}" for p in passages)
                system, user = prompts.render(prompts.TUTOR, learner=json.dumps(snapshot["mastery"]),
                                              misconception=f"{mid}: {mis['incorrect_rule']}", move=f"{style}: {step}",
                                              passages=passages_txt or "(none found)")
                generated = self.llm.complete(session_id=state["session"]["session_id"], node="tutor", role="tutor",
                                              system=system, user=user)
                if generated:
                    text = generated if "[" in generated or not cite else f"{generated}{cite}"
        else:
            question = state["messages"][-1]["content"]
            passages = self._passages_for(state, "tutor", question)
            if not passages:
                chapter = CHAPTERS[state["session"].get("chapter", "quadratic_equations")]
                text, style = (f"I couldn't find that in our chapter material ({chapter}), so I won't guess. "
                               "Could you rephrase it, or type 'practice' for a question?"), "missing_evidence"
            else:
                top = passages[0]
                text = f"Let's think it through. {top['text']} [{top['passage_id']}] What does that suggest for your problem?"
                style = "socratic_question"
        retrieved = [dict(p) for p in passages]
        update = {"draft": {"text": text, "citations": [p["passage_id"] for p in passages], "kind": "hint",
                            "style": style, "misconception_id": mid},
                  "retrieved": retrieved, "hint_stage": stage + 1 if mid and not item else stage}
        if item:
            update["active_item"] = item
        return update

    def _set_question(self, state: TutorState) -> dict:
        plan = state.get("plan") or {}
        focus = state.get("focus_misconception")
        concept = (self.misconceptions[focus]["concept_id"] if focus else None) or \
                  next((s["concept_id"] for s in plan.get("steps", [])), None)
        chapter = state["session"].get("chapter", "quadratic_equations")
        items = self._call(state, "set_question", "question_setter", "question-bank", "list_published",
                           {"concept_id": concept, "mode": "practice"})["items"]
        items = [i for i in items if i.get("chapter") == chapter]
        if not items:
            items = self._call(state, "set_question", "question_setter", "question-bank", "list_published", {"mode": "practice"})["items"]
            items = [i for i in items if i.get("chapter") == chapter]
        attempted = state.get("attempted", [])
        fresh = [i for i in items if i["question_id"] not in attempted] or items
        if not fresh:
            return {"draft": {"text": "There are no teacher-approved practice sets yet. Your teacher needs to approve "
                                      "one in the teacher view first.", "citations": [], "kind": "info"}}
        item = fresh[0]
        self._call(state, "set_question", "question_setter", "math-tools", "solve", {"question_ref": item["question_id"]})
        active = {"question_id": item["question_id"], "prompt": item["prompt"],
                  "set_id": item["set_id"], "set_payload_sha256": item["set_payload_sha256"],
                  "concept_ids": item["problem"]["concept_ids"], "kind": item["answer_contract"]["allowed_kinds"][0],
                  "hint_stages": item["hint_stages"], "hint_stage": 0, "attempts": 0,
                  "supporting_passage_ids": [f"normalized:{c}" for c in item["problem"]["concept_ids"] if f"normalized:{c}" in self.cards]}
        instruction = ("Answer like 'x = 2 or x = -3' (or 'no real roots')." if active['kind'] == 'finite_set'
                       else "Give an exact value, for example -5, 3/4 or sqrt(3)/2.")
        text = (f"Practice ({item['difficulty']['level']}): {item['prompt']}\n"
                f"{instruction} Type 'hint' if you're stuck.")
        return {"active_item": active, "attempted": attempted + [item["question_id"]],
                "draft": {"text": text, "citations": [], "kind": "question"}}

    def _grade(self, state: TutorState) -> dict:
        item = dict(state["active_item"])
        text = state["messages"][-1]["content"]
        result = self._call(state, "grade", "grader", "math-tools", "check_equivalence",
                            {"question_ref": item["question_id"], "response": text})
        update: dict[str, Any] = {"grade": {**result, "question_id": item["question_id"], "concept_ids": item["concept_ids"],
                                            "set_id": item["set_id"], "set_payload_sha256": item["set_payload_sha256"],
                                            "kind": item["kind"]}}
        if not result["scorable"]:
            example = "'x = 2 or x = -3'" if item['kind'] == 'finite_set' else "'-5' or '3/4'"
            update["draft"] = {"text": f"I couldn't read that as an answer ({result['reason']}). "
                                       f"Try again, for example {example}.", "citations": [], "kind": "info"}
            return update
        if result["correct"]:
            update["active_item"] = None
            followup = ("how did you make sure you didn't miss a root?" if item['kind'] == 'finite_set'
                        else "how did you check your reasoning?")
            update["draft"] = {"text": f"Correct: {result['parsed']}. In one sentence, {followup}",
                               "citations": [], "kind": "feedback"}
            return update
        item["attempts"] += 1
        diag = self._call(state, "grade", "grader", "math-tools", "diagnose_response",
                          {"question_ref": item["question_id"], "response": text})["candidates"]
        stages = item["hint_stages"]
        hint = stages[min(item["hint_stage"], len(stages) - 1)]["prompt"]
        item["hint_stage"] = min(item["hint_stage"] + 1, len(stages) - 1)
        update["active_item"] = item
        if diag:
            mid = diag[0]["misconception_id"]
            update["diagnosis"] = {"misconception_id": mid, "status": "suspected", "evidence": [f"rule: {diag[0]['rule']}"]}
            update["focus_misconception"] = mid
            hint = f"{self.concepts[self.misconceptions[mid]['concept_id']]['diagnostic_probe']} {hint}"
        update["draft"] = {"text": f"Not quite: you gave {result['parsed']}. {hint}", "citations": [], "kind": "feedback",
                           "misconception_id": update.get("focus_misconception")}
        return update

    def _quiz_start(self, state: TutorState) -> dict:
        items = self._call(state, "quiz_start", "question_setter", "question-bank", "list_published", {"mode": "quiz"})["items"]
        chapter = state["session"].get("chapter", "quadratic_equations")
        items = [i for i in items if i.get("chapter") == chapter][:3]
        if not items:
            return {"draft": {"text": "There's no teacher-approved quiz yet.", "citations": [], "kind": "info"}}
        for it in items:
            self._call(state, "quiz_start", "question_setter", "math-tools", "solve", {"question_ref": it["question_id"]})
        quiz = {"quiz_id": uuid.uuid4().hex, "items": [{"question_id": i["question_id"], "prompt": i["prompt"], "concept_ids": i["problem"]["concept_ids"],
                           "set_id": i["set_id"], "set_payload_sha256": i["set_payload_sha256"],
                           "kind": i["answer_contract"]["allowed_kinds"][0]} for i in items], "index": 0, "results": []}
        return {"quiz": quiz, "active_item": None,
                "draft": {"text": f"Quiz mode: {len(items)} questions, no hints.\nQ1: {items[0]['prompt']}",
                          "citations": [], "kind": "question"}}

    def _quiz_answer(self, state: TutorState) -> dict:
        quiz = json.loads(json.dumps(state["quiz"]))
        if not quiz.get("quiz_id"):
            # In-progress sessions created before the ledger receive a stable ID.
            quiz["quiz_id"] = uuid.uuid5(uuid.NAMESPACE_URL, "legacy-quiz:" + state["session"]["session_id"]).hex
        current = quiz["items"][quiz["index"]]
        result = self._call(state, "quiz_answer", "grader", "math-tools", "check_equivalence",
                            {"question_ref": current["question_id"], "response": state["messages"][-1]["content"]})
        if not result.get("scorable"):
            return {"quiz": quiz, "draft": {"text": "I could not read that answer. Please enter it in the expected format; this question has not been scored.",
                                            "citations": [], "kind": "info"}}
        quiz["results"].append({"question_id": current["question_id"], "correct": bool(result["correct"]),
                                "scorable": result["scorable"], "concept_ids": current["concept_ids"], "kind": current["kind"]})
        quiz["index"] += 1
        if quiz["index"] < len(quiz["items"]):
            nxt = quiz["items"][quiz["index"]]
            text = f"Recorded. Q{quiz['index'] + 1}: {nxt['prompt']}"
        else:
            score = sum(r["correct"] for r in quiz["results"])
            text = f"Quiz finished: {score}/{len(quiz['results'])}."
        return {"quiz": quiz, "draft": {"text": text, "citations": [], "kind": "question"}}

    def _refuse(self, state: TutorState) -> dict:
        text = ("I can't share answer keys or full solutions. Being a teacher doesn't change that inside the student chat; "
                "teachers use the teacher view after signing in. ")
        item = state.get("active_item")
        if item:
            text += f"Let's keep going together: {item['hint_stages'][min(item['hint_stage'], 2)]['prompt']}"
        elif state.get("quiz"):
            text += "Answer the quiz question as best you can; you'll see your score at the end."
        else:
            text += "What part are you stuck on?"
        self._note(state, "refuse", "role_or_key_request_refused")
        return {"draft": {"text": text, "citations": [], "kind": "refusal"}}

    def _question_revoked(self, state: TutorState) -> dict:
        """Stop a stale or unverifiable question without scoring or showing its content again."""
        return {"active_item": None, "quiz": None,
                "draft": {"text": "This question is no longer available or cannot be verified. Please request a new practice question or quiz.",
                          "citations": [], "kind": "info"}}

    def _handoff(self, state: TutorState) -> dict:
        store.alert(self.conn, "distress_handoff", state["session"]["learner_id"],
                    {"session_id": state["session"]["session_id"], "note": "Immediate human follow-up needed"})
        self._note(state, "handoff", "distress_handoff_raised")
        return {"draft": {"text": guards.HANDOFF_MESSAGE, "citations": [], "kind": "handoff"}}

    def _output_guard(self, state: TutorState) -> dict:
        draft = state["draft"] or {"text": "", "kind": "info"}
        if not self.defences or draft["kind"] in ("question", "handoff"):
            return {"checks": {"skipped": True}}
        checks: dict[str, Any] = {}
        if state.get("unverified_own_problem"):
            checks["unverified_problem"] = "deterministic_only_not_answer_checked"
        refs = []
        if state.get("active_item"):
            refs.append(state["active_item"]["question_id"])
        if state.get("quiz") and state["quiz"]["index"] < len(state["quiz"]["items"]):
            refs.append(state["quiz"]["items"][state["quiz"]["index"]]["question_id"])
        for ref in refs:
            leak = self._call(state, "output_guard", "output_guard", "math-tools", "leak_check",
                              {"question_ref": ref, "text": draft["text"]})
            if leak["leak"]:
                checks["leak"] = leak
        if guards.generic_leak(draft["text"]):
            checks["leak_phrase"] = True
        cites = guards.check_citations(draft["text"], {r["passage_id"] for r in state.get("retrieved", [])})
        if not cites["ok"]:
            checks["citations"] = cites
        checks["ok"] = not ({"leak", "leak_phrase", "citations"} & checks.keys())
        self._note(state, "output_guard", "pass" if checks["ok"] else "fail", checks)
        return {"checks": checks}

    def _after_guard(self, state: TutorState) -> str:
        checks = state.get("checks", {})
        if checks.get("skipped") or checks.get("ok"):
            return "update_memory"
        return "retry" if state.get("revision_count", 0) < SETTINGS.budgets["max_revisions"] else "fallback"

    def _retry(self, state: TutorState) -> dict:
        return {"revision_count": state.get("revision_count", 0) + 1, "notes": state.get("notes", [])}

    def _fallback(self, state: TutorState) -> dict:
        return {"draft": {"text": "Let's slow down and take one step at a time. What is the very first step you would try?",
                          "citations": [], "kind": "fallback"}}

    def _update_memory(self, state: TutorState) -> dict:
        lid = state["session"]["learner_id"]
        snapshot = state["learner"]
        plan = state.get("plan")
        replan_reason = None
        progress = dict(state.get("resolve_progress") or {})
        call = lambda tool, args: self._call(state, "update_memory", "study_planner", "learner-store", tool, args)  # noqa: E731
        grade, draft, diag = state.get("grade"), state.get("draft") or {}, state.get("diagnosis")
        if diag and draft.get("kind") in ("probe", "feedback") and diag.get("evidence"):
            status = "confirmed" if snapshot["misconceptions"].get(diag["misconception_id"]) else "suspected"
            call("record_misconception", {"learner_id": lid, "misconception_id": diag["misconception_id"],
                                          "status": status, "evidence_ref": "; ".join(diag["evidence"])[:200]})
            mis_concept = self.misconceptions[diag["misconception_id"]]["concept_id"]
            if plan and mis_concept not in [s["concept_id"] for s in plan.get("steps", [])]:
                replan_reason = f"new misconception {diag['misconception_id']} on {mis_concept}"
        if draft.get("kind") == "hint" and draft.get("misconception_id") and draft.get("style") not in ("extension",):
            call("record_misconception", {"learner_id": lid, "misconception_id": draft["misconception_id"],
                                          "status": "addressed", "evidence_ref": f"targeted hint ({draft['style']})"})
        graded = []
        if grade and grade.get("scorable"):
            graded.append(grade)
        quiz = state.get("quiz")
        quiz_done = bool(quiz) and quiz["index"] >= len(quiz["items"])
        mastery = dict(snapshot["mastery"])
        for g in graded:
            for cid in g["concept_ids"]:
                if cid not in self.concepts:
                    continue
                before = mastery.get(cid, SETTINGS.learner_model["p_init"])
                after = learner.bkt_update(before, bool(g["correct"]), GUESS_BY_KIND.get(g["kind"]))
                mastery[cid] = after
                call("update_mastery", {"learner_id": lid, "concept_id": cid, "p_mastery": after,
                                        "evidence_ref": f"{g['question_id']}:{'correct' if g['correct'] else 'incorrect'}"})
                if g["correct"] and store.resolve_stuck_concept(self.conn, lid, cid):
                    self._note(state, "update_memory", "stuck_episode_closed", {"concept_id": cid})
                if not g["correct"] and plan and cid in plan.get("mastered", []):
                    replan_reason = f"contradiction: failed {cid}, which the plan assumed was mastered"
            focus = state.get("focus_misconception")
            if focus and grade and g is grade:
                style = next((s["style"] for s in snapshot.get("styles", []) if s["misconception_id"] == focus), None)
                call("record_explanation", {"learner_id": lid, "misconception_id": focus,
                                            "style": style or "socratic_question", "success": bool(g["correct"])})
                if g["correct"]:
                    progress[focus] = progress.get(focus, 0) + 1
                    if progress[focus] >= 2:
                        call("record_misconception", {"learner_id": lid, "misconception_id": focus, "status": "resolved",
                                                      "evidence_ref": "two later correct answers"})
        quiz_application = None
        if quiz_done:
            if quiz.get("quiz_id"):
                quiz_application = call("apply_quiz", {"learner_id": lid, "quiz_id": quiz["quiz_id"],
                                                       "results": quiz["results"],
                                                       "chapter": state["session"].get("chapter", "quadratic_equations")})
                for concept in quiz_application.get("resolved_concepts", []):
                    self._note(state, "update_memory", "stuck_episode_closed", {"concept_id": concept})
                self._note(state, "update_memory", "quiz_applied" if quiz_application["applied"] else "quiz_already_applied",
                           {"quiz_id": quiz["quiz_id"]})
            else:
                # A finished checkpoint from an older build cannot tell us if
                # it already committed updates. Do not risk applying it twice.
                self._note(state, "update_memory", "legacy_quiz_not_replayed")
        # An explicit self-reported stuck signal on a registered problem counts
        # once per distinct session. Infer the concept only when unambiguous.
        item = state.get("active_item") or {}
        message = (state.get("messages") or [{}])[-1].get("content", "")
        if draft.get("kind") == "hint" and STUCK_SIGNAL.search(message) and item.get("concept_ids"):
            candidates = set(item["concept_ids"])
            focus = state.get("focus_misconception")
            if focus in self.misconceptions and self.misconceptions[focus]["concept_id"] in candidates:
                candidates = {self.misconceptions[focus]["concept_id"]}
            elif len(candidates) > 1:
                candidates = {self.misconceptions[mid]["concept_id"] for mid, observed in snapshot["misconceptions"].items()
                              if mid in self.misconceptions and observed["status"] in ("suspected", "confirmed", "addressed")
                              and self.misconceptions[mid]["concept_id"] in candidates}
            if len(candidates) == 1:
                concept = next(iter(candidates))
                created = store.record_stuck_session(self.conn, lid, concept, state["session"]["session_id"])
                self._note(state, "update_memory", "stuck_signal_recorded",
                           {"concept_id": concept, "local_teacher_event_created": created})
        fresh = call("read_learner", {"learner_id": lid})
        update: dict[str, Any] = {"learner": fresh, "resolve_progress": progress}
        if quiz_done and quiz_application is not None:
            chapter = state["session"].get("chapter", "quadratic_equations")
            current_plan = (fresh.get("plan") if chapter == "quadratic_equations"
                            else fresh.get("topic_plans", {}).get(chapter))
            update["plan"] = current_plan
            if current_plan and quiz_application["applied"]:
                reason = current_plan.get("replan_reason")
                update["notes"] = (state.get("notes") or []) + [f"Study plan updated (v{current_plan['version']}): {reason}."]
                self._note(state, "update_memory", "replan", {"version": current_plan["version"], "reason": reason})
            elif not quiz_application["applied"]:
                update["notes"] = (state.get("notes") or []) + ["This quiz was already recorded; your current plan was preserved."]
        elif quiz_done:
            update["draft"] = {"text": "This older quiz could not be safely recorded. Please start a new quiz.", "citations": [], "kind": "info"}
            update["notes"] = (state.get("notes") or []) + ["This older quiz could not be safely replayed. Please start a new quiz."]
        elif replan_reason:
            new_plan = learner.make_plan(fresh, previous=plan, reason=replan_reason)
            call("save_plan", {"learner_id": lid, "plan": new_plan})
            update["plan"] = new_plan
            update["notes"] = (state.get("notes") or []) + [f"Study plan updated (v{new_plan['version']}): {replan_reason}."]
            self._note(state, "update_memory", "replan", {"version": new_plan["version"], "reason": replan_reason})
        if quiz_done:
            update["quiz"] = None
        return update

    def _respond(self, state: TutorState) -> dict:
        draft = state.get("draft") or {"text": "…"}
        notes = state.get("notes") or []
        text = draft["text"] + ("".join(f"\n({n})" for n in notes) if notes else "")
        cited = set(guards.check_citations(text, set())["cited"])
        citations = []
        for ref in state.get("retrieved", []):
            if ref.get("passage_id") not in cited or not isinstance(ref.get("text"), str):
                continue
            source = ref.get("source") if isinstance(ref.get("source"), dict) else {}
            citation = {"passage_id": ref["passage_id"], "title": ref.get("title"),
                        "concept_id": ref.get("concept_id"), "text": ref["text"],
                        "chapter": ref.get("chapter"), "review_status": ref.get("review_status", "unavailable"),
                        "source": {"source_id": source.get("source_id"), "source_sha256": source.get("source_sha256"),
                                   "url": source.get("url"), "page": source.get("page"),
                                   "pdf_page": source.get("pdf_page"), "section": source.get("section")}}
            citation["reference_sha256"] = hashlib.sha256(store.dumps(citation).encode("utf-8")).hexdigest()
            citations.append(citation)
        return {"messages": [{"role": "tutor", "content": text, "kind": draft.get("kind"), "citations": citations}]}

    def _build_session_graph(self) -> StateGraph:
        g = StateGraph(TutorState)
        g.add_node("input_guard", self._input_guard)
        g.add_node("load_learner", self._load_learner)
        g.add_node("planner", self._planner)
        g.add_node("diagnose", self._diagnose)
        g.add_node("tutor", self._tutor)
        g.add_node("tutor_extension", lambda s: self._tutor(s, extension=True))
        g.add_node("set_question", self._set_question)
        g.add_node("grade", self._grade)
        g.add_node("quiz_start", self._quiz_start)
        g.add_node("quiz_answer", self._quiz_answer)
        g.add_node("refuse", self._refuse)
        g.add_node("handoff", self._handoff)
        g.add_node("question_revoked", self._question_revoked)
        g.add_node("output_guard", self._output_guard)
        g.add_node("retry", self._retry)
        g.add_node("fallback", self._fallback)
        g.add_node("update_memory", self._update_memory)
        g.add_node("respond", self._respond)
        g.add_edge(START, "input_guard")
        g.add_edge("input_guard", "load_learner")
        g.add_edge("load_learner", "planner")
        specialists = ["diagnose", "tutor", "tutor_extension", "set_question", "grade", "quiz_start", "quiz_answer",
                       "refuse", "handoff", "question_revoked"]
        g.add_conditional_edges("planner", lambda s: s["route"], {n: n for n in specialists})
        for n in specialists:
            g.add_edge(n, "output_guard")
        g.add_conditional_edges("output_guard", self._after_guard,
                                {"update_memory": "update_memory", "retry": "retry", "fallback": "fallback"})
        g.add_edge("retry", "tutor")
        g.add_edge("fallback", "update_memory")
        g.add_edge("update_memory", "respond")
        g.add_edge("respond", END)
        return g

    # ------------------------------------------------------------------ public API: student turns
    def turn(self, session_id: str, learner_id: str, text: str, mode: str = "practice", chapter: str | None = None) -> dict:
        try:
            with self.bus.publication_lock:
                return self._turn_locked(session_id, learner_id, text, mode, chapter)
        except Timeout as exc:
            raise ToolCallError("BUSY", "publication is busy; please retry") from exc

    def _turn_locked(self, session_id: str, learner_id: str, text: str, mode: str, chapter: str | None = None) -> dict:
        screen = guards.screen_input(text) if self.defences else {"text": text}
        config = {"configurable": {"thread_id": session_id}}
        prior = self.graph.get_state(config)
        old_session = (prior.values or {}).get("session") if prior else None
        old_chapter = (old_session or {}).get("chapter", "quadratic_equations")
        if old_session and chapter is not None and chapter != old_chapter:
            raise ValueError("A conversation cannot change its chapter; start a new conversation.")
        selected = old_chapter if old_session else (chapter or "quadratic_equations")
        if selected not in CHAPTERS:
            raise ValueError("Unknown chapter")
        state = self.graph.invoke({"incoming": screen["text"], "screen": screen,
                                   "session": {"session_id": session_id, "learner_id": learner_id, "mode": mode,
                                               "chapter": selected}}, config)
        ctx = self._ctx.get(session_id)
        tools = list(ctx.log) if ctx else []
        if ctx:
            ctx.log.clear()
        return {"reply": state["messages"][-1]["content"], "route": state.get("route"), "plan": state.get("plan"),
                "diagnosis": state.get("diagnosis"), "checks": state.get("checks"), "tools": tools,
                "citations": state["messages"][-1].get("citations", []),
                "active_item": (state.get("active_item") or {}).get("question_id")}

    def resume(self, session_id: str) -> dict | None:
        """Resume a checkpoint only while its referenced question approvals remain valid."""
        try:
            with self.bus.publication_lock:
                config = {"configurable": {"thread_id": session_id}}
                snap = self.graph.get_state(config)
                if not snap.next:
                    return None
                if self._publication_unavailable(snap.values, include_completed=True):
                    text = "This question is no longer available or cannot be verified. Please request a new practice question or quiz."
                    # Mark the interrupted graph complete without executing its pending nodes.
                    self.graph.update_state(config, {"active_item": None, "quiz": None, "grade": None,
                                                    "route": "question_revoked", "draft": None,
                                                    "messages": [{"role": "tutor", "content": text, "kind": "info"}]},
                                            as_node="respond")
                    return {"reply": text, "resumed_from": list(snap.next), "revoked": True}
                state = self.graph.invoke(None, config)
                return {"reply": state["messages"][-1]["content"], "resumed_from": list(snap.next)}
        except Timeout as exc:
            raise ToolCallError("BUSY", "publication is busy; please retry") from exc

    def history(self, session_id: str) -> list[dict]:
        snap = self.graph.get_state({"configurable": {"thread_id": session_id}})
        return (snap.values or {}).get("messages", []) if snap else []

    # ------------------------------------------------------------------ teacher approval graph
    def _qs_ctx(self, state: ApprovalState) -> dict:
        return {"session": {"session_id": state["thread_id"], "learner_id": None}}

    def _qs_start(self, state: ApprovalState) -> dict:
        s = self._qs_ctx(state)
        if state.get("set_id") and state.get("edit_question_ids"):
            res = self._call(s, "qs_start", "approval_gate", "question-bank", "update_proposal",
                             {"set_id": state["set_id"], "question_ids": state["edit_question_ids"], "thread_id": state["thread_id"]})
            return {"payload_sha256": res["payload_sha256"], "edit_question_ids": None, "status": "pending"}
        if state.get("set_id"):
            prop = self._call(s, "qs_start", "approval_gate", "question-bank", "get_proposal", {"set_id": state["set_id"]})
            return {"payload_sha256": prop["payload_sha256"], "status": "pending"}
        published = {i["question_id"] for i in
                     self._call(s, "qs_start", "question_setter", "question-bank", "list_published", {})["items"]}
        pool = self._call(s, "qs_start", "question_setter", "question-bank", "candidate_items",
                          {"concept_id": state["concept_id"], "mode": state.get("mode", "practice")})["question_ids"]
        chosen = [q for q in pool if q not in published][:3] or pool[:3]
        set_id = f"set-{uuid.uuid4().hex[:8]}"
        res = self._call(s, "qs_start", "question_setter", "question-bank", "propose_set",
                         {"set_id": set_id, "concept_id": state["concept_id"], "question_ids": chosen,
                          "rationale": f"{state.get('mode', 'practice').title()} for {state['concept_id']}", "thread_id": state["thread_id"]})
        return {"set_id": set_id, "payload_sha256": res["payload_sha256"], "status": "pending"}

    def _qs_validate(self, state: ApprovalState) -> dict:
        s = self._qs_ctx(state)
        prop = self._call(s, "qs_validate", "approval_gate", "question-bank", "get_proposal", {"set_id": state["set_id"]})
        for item in prop["payload"]["items"]:
            self._call(s, "qs_validate", "approval_gate", "math-tools", "solve", {"question_ref": item["question_id"]})
        return {"payload_sha256": prop["payload_sha256"]}

    def _qs_gate(self, state: ApprovalState) -> dict:
        decision = interrupt({"set_id": state["set_id"], "payload_sha256": state["payload_sha256"]})
        return {"decision": decision}

    def _qs_route(self, state: ApprovalState) -> str:
        return {"approve": "qs_publish", "edit": "qs_edit", "reject": "qs_reject"}[state["decision"]["decision"]]

    def _qs_publish(self, state: ApprovalState) -> dict:
        teacher = state["decision"]["teacher_id"]
        token = approval_token.mint(state["payload_sha256"], teacher)
        self._call(self._qs_ctx(state), "qs_publish", "approval_gate", "question-bank", "publish_approved_set",
                   {"set_id": state["set_id"], "approval_token": token, "teacher_id": teacher})
        return {"status": "published", "token": token}

    def _qs_edit(self, state: ApprovalState) -> dict:
        res = self._call(self._qs_ctx(state), "qs_edit", "approval_gate", "question-bank", "update_proposal",
                         {"set_id": state["set_id"], "question_ids": state["decision"]["question_ids"],
                          "thread_id": state["thread_id"]})
        return {"payload_sha256": res["payload_sha256"], "status": "pending"}

    def _qs_reject(self, state: ApprovalState) -> dict:
        self._call(self._qs_ctx(state), "qs_reject", "approval_gate", "question-bank", "reject_proposal",
                   {"set_id": state["set_id"], "reason": state["decision"].get("reason", "")})
        return {"status": "rejected"}

    def _build_approval_graph(self) -> StateGraph:
        g = StateGraph(ApprovalState)
        for name, fn in [("qs_start", self._qs_start), ("qs_validate", self._qs_validate), ("qs_gate", self._qs_gate),
                         ("qs_publish", self._qs_publish), ("qs_edit", self._qs_edit), ("qs_reject", self._qs_reject)]:
            g.add_node(name, fn)
        g.add_edge(START, "qs_start")
        g.add_edge("qs_start", "qs_validate")
        g.add_edge("qs_validate", "qs_gate")
        g.add_conditional_edges("qs_gate", self._qs_route, ["qs_publish", "qs_edit", "qs_reject"])
        g.add_edge("qs_edit", "qs_validate")
        g.add_edge("qs_publish", END)
        g.add_edge("qs_reject", END)
        return g

    def propose_set(self, concept_id: str, mode: str = "practice") -> dict:
        thread_id = f"qs-{uuid.uuid4().hex[:8]}"
        out = self.approval.invoke({"concept_id": concept_id, "mode": mode, "thread_id": thread_id},
                                   {"configurable": {"thread_id": thread_id}})
        return {"set_id": out["set_id"], "payload_sha256": out["payload_sha256"], "thread_id": thread_id,
                "waiting_for_teacher": bool(out.get("__interrupt__"))}

    def proposal(self, set_id: str) -> dict:
        return self.bus.call(CallContext(session_id="teacher"), "approval_gate", "question-bank", "get_proposal",
                             {"set_id": set_id})

    def decide(self, set_id: str, decision: str, teacher_id: str, question_ids: list[str] | None = None,
               reason: str | None = None) -> dict:
        prop = self.proposal(set_id)
        config = {"configurable": {"thread_id": prop["thread_id"]}}
        waiting = bool(self.approval.get_state(config).next)
        if decision == "edit" and not waiting:  # editing a published/rejected set starts a new review thread
            thread_id = f"qs-{uuid.uuid4().hex[:8]}"
            out = self.approval.invoke({"set_id": set_id, "thread_id": thread_id, "edit_question_ids": question_ids},
                                       {"configurable": {"thread_id": thread_id}})
            return {"set_id": set_id, "status": "pending", "payload_sha256": out["payload_sha256"], "thread_id": thread_id}
        if not waiting:
            return {"set_id": set_id, "status": prop["status"], "error": "this set is not waiting for a decision"}
        out = self.approval.invoke(Command(resume={"decision": decision, "teacher_id": teacher_id,
                                                   "question_ids": question_ids, "reason": reason}), config)
        return {"set_id": set_id, "status": out.get("status"), "payload_sha256": out.get("payload_sha256"),
                "token": out.get("token")}

    def try_publish(self, set_id: str, token: str, teacher_id: str) -> dict:
        try:
            return self.bus.call(CallContext(session_id="teacher"), "approval_gate", "question-bank",
                                 "publish_approved_set", {"set_id": set_id, "approval_token": token, "teacher_id": teacher_id})
        except ToolCallError as exc:
            return {"published": False, "error": str(exc)}

    def close(self) -> None:
        if getattr(self, "_closed", False):
            return
        self.bus.close()
        self.checkpointer.conn.close()
        self.conn.close()
        self._closed = True
