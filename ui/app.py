"""Streamlit UI for the Socratic Tutor. It only talks to the API; it holds no tutor code or answer keys.

Run: streamlit run ui/app.py   (with the API on TUTOR_API_URL, default http://localhost:8000)
The pages shown depend on the role the API reports for the token you sign in with.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from urllib.parse import quote, urlsplit

import requests
import streamlit as st

API = os.environ.get("TUTOR_API_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 120
CHAPTER_LABELS = {
    "quadratic_equations": "Quadratic Equations",
    "arithmetic_progressions": "Arithmetic Progressions",
    "trigonometry": "Introduction to Trigonometry",
}

st.set_page_config(page_title="Socratic Tutor", page_icon="ðŸ“", layout="wide")


# ---------------------------------------------------------------------- API helpers
def call(method: str, path: str, **kwargs):
    headers = {"Authorization": f"Bearer {st.session_state.get('token', '')}"}
    try:
        r = requests.request(method, f"{API}{path}", headers=headers, timeout=TIMEOUT, **kwargs)
    except requests.RequestException as exc:
        st.error(f"Cannot reach the API at {API}: {exc}")
        return None
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text
        st.error(f"{r.status_code}: {detail}")
        return None
    return r.json()


def stream_chat(text: str, mode: str):
    """Stream one request; keep a known reference for recovery and source snapshots."""
    st.session_state.setdefault("session_id", uuid.uuid4().hex)
    body = {"text": text, "mode": mode, "session_id": st.session_state["session_id"],
            "chapter": st.session_state.get("chat_chapter", "quadratic_equations")}
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    st.session_state["last_citations"] = []
    st.session_state["last_result"] = None
    st.session_state["chat_error"] = None
    try:
        with requests.post(f"{API}/chat/stream", json=body, headers=headers, stream=True, timeout=TIMEOUT) as response:
            if response.status_code >= 400:
                st.session_state["chat_error"] = ("This conversation needs recovery before you continue." if response.status_code == 409 else
                                                  "I couldn't send that message. Check your access and try again.")
                st.session_state["needs_recovery_check"] = True
                return
            event = None
            for line in response.iter_lines(decode_unicode=True):
                if line.startswith("event: "):
                    event = line[7:]
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
                    if event == "token":
                        yield data["text"]
                    elif event == "plan":
                        st.session_state["plan"] = data
                    elif event == "citation":
                        st.session_state["last_citations"].append(data)
                    elif event == "done":
                        st.session_state["session_id"] = data["session_id"]
                        st.session_state["last_result"] = data
                        was_quiz = st.session_state.get("quiz_active", False)
                        st.session_state["quiz_active"] = bool(data.get("quiz_active"))
                        if was_quiz and not data.get("quiz_active"):
                            st.session_state["pending_mode"] = "practice"
                    elif event == "error":
                        st.session_state["chat_error"] = "That turn was interrupted. Try resuming it before sending the same message again."
                        st.session_state["needs_recovery_check"] = True
    except (requests.RequestException, ValueError):
        st.session_state["chat_error"] = "The connection was interrupted. Try resuming this conversation before sending the same message again."
        st.session_state["needs_recovery_check"] = True
    if not st.session_state.get("last_result") and not st.session_state.get("chat_error"):
        st.session_state["chat_error"] = "The reply did not finish. Try resuming this conversation."
        st.session_state["needs_recovery_check"] = True


def display_reply(content: str, references: list[dict]) -> str:
    """Readable source labels; preserve the saved raw response and maths brackets."""
    labels = {ref["passage_id"]: f"Reference {index}" for index, ref in enumerate(references, 1)}
    return re.sub(r"\[((?:normalized|ncert|exemplar):[^]\s]+)\]",
                  lambda match: f"[{labels[match[1]]}]" if match[1] in labels else match[0], content)


def show_references(references: list[dict]) -> None:
    for index, ref in enumerate(references, 1):
        with st.expander(f"Reference {index}: {ref.get('title') or 'Chapter material'}"):
            st.markdown(ref.get("text") or "")
            source = ref.get("source") or {}
            location = source.get("page") or source.get("pdf_page")
            if location is not None:
                st.caption(f"Page {location}")
            url = source.get("url") or ""
            if urlsplit(url).scheme in ("http", "https") and urlsplit(url).netloc:
                st.markdown(f"[Open original reference]({url})")


# ---------------------------------------------------------------------- sign-in
with st.sidebar:
    st.title("Socratic Tutor")
    token = st.text_input("Access token", value=st.session_state.get("token", os.environ.get("TUTOR_UI_TOKEN", "")),
                          type="password", help="Dev tokens: dev-student-a, dev-student-b, dev-teacher")
    if token != st.session_state.get("token"):
        st.session_state.clear()
        st.session_state["token"] = token
    me = call("GET", "/me") if token else None
    if me:
        st.caption(f"Signed in as **{me['id']}** ({me['role']})")
    st.caption(f"API: {API}")

if not me:
    st.info("Enter an access token in the sidebar to start.")
    st.stop()


# ---------------------------------------------------------------------- pages
def learner_overview(learner_id: str) -> None:
    data = call("GET", f"/learners/{learner_id}")
    if not data:
        return
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Mastery")
        if data["mastery"]:
            st.bar_chart({k: v for k, v in sorted(data["mastery"].items())}, horizontal=True)
        else:
            st.caption("No mastery estimates yet.")
    with c2:
        st.subheader("Misconceptions")
        rows = [{"misconception": k, **v} for k, v in data["misconceptions"].items()]
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        else:
            st.caption("None on record.")
        st.subheader("Alerts")
        if data["alerts"]:
            st.dataframe(data["alerts"], hide_index=True, width="stretch")
        else:
            st.caption("No alerts.")
    if data.get("plan"):
        with st.expander(f"Study plan v{data['plan'].get('version')}"):
            for i, step in enumerate(data["plan"].get("steps", []), 1):
                st.markdown(f"{i}. **{step['concept_id']}** {step.get('title', '')}: {step.get('action', '')}")


def restore_active_conversation() -> None:
    """Restore only the signed-in learner's server-owned unfinished conversation."""
    if st.session_state.get("active_checked") and not st.session_state.pop("needs_recovery_check", False):
        return
    active = call("GET", "/chat/active")
    st.session_state["active_checked"] = True
    st.session_state["interrupted"] = bool(active and active.get("interrupted"))
    if not active or not active.get("session_id"):
        return
    history = call("GET", "/chat/" + quote(active["session_id"], safe="") + "/history")
    if history:
        st.session_state["session_id"] = active["session_id"]
        st.session_state["messages"] = history.get("messages", [])
        st.session_state["chat_chapter"] = history["chapter"]
        st.session_state["quiz_active"] = bool(active.get("quiz_active"))
        if active.get("interrupted"):
            st.session_state["chat_error"] = "A previous turn was interrupted. Resume it before sending another message."


def student_chat() -> None:
    restore_active_conversation()
    if "pending_mode" in st.session_state:
        st.session_state["chat_mode"] = st.session_state.pop("pending_mode")
    if st.session_state.get("quiz_active"):
        st.session_state["chat_mode"] = "quiz"
    st.header("Chat with your tutor")
    st.caption("Work through one step at a time. Ask a question, try a hint, or practise a checked problem.")
    controls = st.columns([2, 1, 1])
    unfinished = bool(st.session_state.get("quiz_active") or st.session_state.get("interrupted"))
    if controls[2].button("New session", disabled=unfinished):
        for key in ("session_id", "messages", "plan", "last_citations", "last_result", "chat_error", "quiz_active", "interrupted"):
            st.session_state.pop(key, None)
    chapter = controls[0].selectbox("Chapter", list(CHAPTER_LABELS), format_func=CHAPTER_LABELS.get,
                                  key="chat_chapter", disabled=bool(st.session_state.get("session_id")),
                                  help="Start a new session to switch chapters.")
    mode = controls[1].radio("Mode", ["practice", "quiz"], horizontal=True,
                            format_func=lambda value: "Practice" if value == "practice" else "Quiz", key="chat_mode",
                            disabled=bool(st.session_state.get("quiz_active")))
    if mode == "quiz":
        st.caption("Quiz mode uses approved questions and does not give hints.")
    if st.session_state.get("quiz_active"):
        st.info("Finish this quiz or leave it without a score before starting a new conversation.")
        if st.button("Leave quiz without scoring", disabled=bool(st.session_state.get("interrupted"))):
            out = call("POST", "/chat/leave", json={"session_id": st.session_state["session_id"]})
            if out:
                history = call("GET", "/chat/" + quote(st.session_state["session_id"], safe="") + "/history")
                if history:
                    st.session_state["messages"] = history.get("messages", [])
                st.session_state["quiz_active"] = False
                st.session_state["last_result"] = None
                st.session_state["pending_mode"] = "practice"
                st.session_state["chat_error"] = None
                st.rerun()
    health = call("GET", "/health")
    if health and not health.get("model_enabled"):
        st.caption("Reference mode: source explanations and checked practice are available without a live tutor.")
    with st.expander("Conversation details and recovery"):
        st.caption(f"Conversation reference: {st.session_state.get('session_id', 'not started')}")
        if st.button("Resume interrupted turn", disabled=not st.session_state.get("session_id")):
            out = call("POST", "/chat/resume", json={"session_id": st.session_state["session_id"]})
            if out:
                st.toast("Resumed." if out["resumed"] else "Nothing to resume.")
                # The server may have finished before the connection dropped.
                # Reload its saved reply even when no graph nodes need resuming.
                history = call("GET", "/chat/" + quote(st.session_state["session_id"], safe="") + "/history")
                if history:
                    st.session_state["messages"] = history.get("messages", [])
                    st.session_state["chat_error"] = None
                    st.session_state["interrupted"] = False
                    st.session_state["active_checked"] = False
                    st.rerun()
    chat_col, side = st.columns([3, 1])
    with chat_col:
        messages = st.session_state.setdefault("messages", [])
        if not messages:
            examples = {"quadratic_equations": "Why might dividing by x lose a possible solution?",
                        "arithmetic_progressions": "Can an arithmetic progression decrease?",
                        "trigonometry": "How do I choose the opposite and adjacent sides?"}
            st.info(f"Start with a question about {CHAPTER_LABELS[chapter]}. For example: {examples[chapter]}")
        for message in messages:
            with st.chat_message("user" if message["role"] == "student" else "assistant"):
                refs = message.get("citations", [])
                st.markdown(display_reply(message["content"], refs))
                show_references(refs)
        if st.session_state.get("chat_error"):
            st.error(st.session_state["chat_error"])
        if prompt := st.chat_input("Ask a question, enter an answer, or type 'practice'",
                                   disabled=bool(st.session_state.get("interrupted"))):
            messages.append({"role": "student", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                reply = st.write_stream(stream_chat(prompt, mode))
            if st.session_state.get("last_result") and not st.session_state.get("chat_error"):
                messages.append({"role": "tutor", "content": reply,
                                 "citations": list(st.session_state.get("last_citations", []))})
            st.rerun()
    with side:
        st.subheader("Your next steps")
        plan = st.session_state.get("plan")
        if plan and plan.get("steps"):
            for index, step in enumerate(plan["steps"], 1):
                st.markdown(f"**{index}. {step.get('title') or 'Chapter practice'}**")
                st.write(step.get("action", "practise").replace("_", " ").capitalize())
                if step.get("why"):
                    st.caption(step["why"])
        else:
            st.caption("Try a short quiz to build a plan from your checked work.")


def teacher_approvals() -> None:
    st.header("Question-set approvals")
    with st.form("propose"):
        concept = st.text_input("Concept ID", value="qe04")
        mode = st.selectbox("Intended use", ["practice", "quiz", "diagnostic"])
        if st.form_submit_button("Propose a set") and concept:
            out = call("POST", "/teacher/proposals", json={"concept_id": concept, "mode": mode})
            if out:
                st.success(f"Proposed {out['set_id']}")
    data = call("GET", "/teacher/proposals")
    proposals = (data or {}).get("proposals", [])
    if not proposals:
        st.caption("No proposals yet.")
        return
    st.dataframe(proposals, hide_index=True, width="stretch",
                 column_order=["set_id", "concept_id", "status", "revision", "payload_sha256"])
    set_id = st.selectbox("Review a set", [p["set_id"] for p in proposals])
    prop = call("GET", f"/teacher/proposals/{set_id}") if set_id else None
    if not prop:
        return
    st.markdown(f"**{set_id}** Â· status `{prop['status']}` Â· revision {prop['revision']}  \n"
                f"payload sha256 `{prop['payload_sha256']}`")
    items = prop["payload"]["items"]
    for item in items:
        st.markdown(f"- `{item['question_id']}` {item['prompt']} — allowed: {', '.join(item.get('mode_policy', {}).get('allowed_modes', []))}; content review: {item.get('review_status') or 'not recorded'}; authorship: {item.get('authorship') or 'not recorded'}")
    pool = call("GET", "/teacher/items", params={"concept_id": prop["payload"]["concept_id"]}) or {"items": []}
    options = sorted({i["question_id"] for i in pool["items"]} | {i["question_id"] for i in items})
    chosen = st.multiselect("Items (edit to change the set)", options, default=[i["question_id"] for i in items])
    reason = st.text_input("Reason (for reject)")
    b1, b2, b3 = st.columns(3)
    result = None
    if b1.button("Approve", type="primary"):
        result = call("POST", f"/teacher/proposals/{set_id}/approve")
    if b2.button("Save edit"):
        result = call("POST", f"/teacher/proposals/{set_id}/edit", json={"question_ids": chosen})
    if b3.button("Reject"):
        result = call("POST", f"/teacher/proposals/{set_id}/reject", json={"reason": reason})
    if result:
        st.json(result)
        if result.get("token"):
            st.session_state["last_token"] = (set_id, result["token"])
    if st.session_state.get("last_token", (None,))[0] == set_id:
        with st.expander("Try publishing with the last approval token"):
            st.caption("After an edit, the old token must fail: the payload hash changed.")
            if st.button("Try publish"):
                st.json(call("POST", f"/teacher/proposals/{set_id}/try-publish",
                             json={"token": st.session_state["last_token"][1]}) or {})


def student_progress() -> None:
    st.header("My progress")
    learner_overview(me["id"])


def teacher_learners() -> None:
    st.header("Learner overview")
    learners = (call("GET", "/learners") or {}).get("learners", [])
    if not learners:
        st.caption("No learners.")
        return
    lid = st.selectbox("Learner", [l["learner_id"] for l in learners],
                       format_func=lambda x: next(f"{l['learner_id']} ({l['alias']})" for l in learners
                                                  if l["learner_id"] == x))
    learner_overview(lid)


def teacher_privacy() -> None:
    st.header("Learner data requests")
    st.write("Delete a signed-in learning record only after confirming the learner's request and your authority to act.")
    st.caption("This removes the connected learning history and progress. Anonymous browser history, backups and downloaded copies are separate.")
    lid = st.text_input("Learner ID for deletion", key="delete_learner_id").strip()
    confirmation = st.text_input("Type the learner ID again", key="delete_confirmation").strip()
    authorized = st.checkbox("I have confirmed this request and am authorized to delete this record.")
    if st.button("Delete connected learning record", disabled=not (lid and lid == confirmation and authorized)):
        receipt = call("DELETE", "/learners/" + quote(lid, safe=''))
        if receipt:
            st.success("The connected learning record was deleted. Keep the receipt for this request.")
            st.json(receipt)


def teacher_trace() -> None:
    st.header("Connected session trace")
    st.caption("Use the conversation reference from the connected learner screen. The timeline shows model, tool and guard events; prompts, answer keys and tool payloads are withheld.")
    sid = st.text_input("Conversation reference", key="teacher_trace_session").strip()
    if st.button("Load session trace", disabled=not sid):
        trace = call("GET", "/teacher/sessions/" + quote(sid, safe='') + "/trace")
        if trace:
            st.caption("Registered-question hint mode: " + trace["registered_hint_mode"])
            if trace["truncated"]:
                st.info("Showing the most recent 200 events.")
            st.dataframe(trace["events"], hide_index=True, width="stretch")
            st.subheader("Citations by tutor turn")
            if trace["cited_turns_truncated"]:
                st.info("Showing the most recent 50 cited turns.")
            if trace["cited_turns"]:
                st.dataframe([{"turn": t["message_index"], "kind": t["kind"], **c}
                              for t in trace["cited_turns"] for c in t["citations"]], hide_index=True, width="stretch")
            else:
                st.caption("No tutor turn in this conversation carried a citation.")
            st.json({"latest_message_citation_refs": trace["citation_refs"]})


if me["role"] == "teacher":
    pages = [st.Page(teacher_approvals, title="Approvals", url_path="approvals"),
             st.Page(teacher_learners, title="Learners", url_path="learners"),
             st.Page(teacher_privacy, title="Data requests", url_path="data-requests"),
             st.Page(teacher_trace, title="Session trace", url_path="session-trace")]
else:
    pages = [st.Page(student_chat, title="Chat", url_path="chat"),
             st.Page(student_progress, title="My progress", url_path="progress")]
st.navigation(pages).run()
