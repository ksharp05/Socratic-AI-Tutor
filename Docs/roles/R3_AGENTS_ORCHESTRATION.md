# R3 · Agents and orchestration engineer · Poonam Prajapati

**What the guide asks** (lectures L8 and L10–L12):
- a LangGraph graph with typed state, conditional edges, a self-correction loop and a persistent checkpointer, with stop-and-resume;
- a plan object shown to the user, and a replan when a result contradicts it;
- a supervisor with at least three specialists, plus a single-agent baseline;
- a Reflexion loop that writes reviewed lessons.

## What exists

| Piece | Where |
|---|---|
| Session graph: input guard → load learner → planner → specialist → output guard (one retry, then fallback) → memory; SQLite checkpointer | `src/tutor/app.py` |
| Specialists: diagnostician, tutor, grader, question setter, plus converse, refuse and hand off | `src/tutor/app.py`, `src/tutor/prompts.py` |
| Study plan over the concept graph, with a replan on contradiction ("Study plan updated (v2)") | `src/tutor/learner.py`, `app.py` |
| Teacher approval graph with `interrupt()` | `src/tutor/app.py`, `approval_token.py` |
| Arms c0 (fixed workflow), c1 (single agent) and c2 (team) for E1 | `eval/configs/m3_live_c*.toml` |
| Candidate Reflexion playbook (4 lessons) | `eval/fixtures/m3_candidate_playbook.json` |
| **After-last-hint worked example (TP-A2), revisit marks, empty-set answers, model-written diagnosis question behind a check** | `src/tutor/app.py`, `mathcore.py` |
| **Architecture diagram and numbered walkthrough of a real trace** | `Docs/report/ARCHITECTURE.md` |
| **Report sections 2 and 6; specialists proposal** | Report; `Docs/m3/R3_SPECIALISTS.md` |
| **C2 review of step feedback, with 174 tests** | `Docs/m3/R3_C2_STEP_FEEDBACK_REVIEW.md`, `tests/test_r3_step_feedback.py` |

## Who built it

| Built by | What |
|---|---|
| **Poonam** (about 30 commits, 3–13 Nov) | Everything in bold above. Also the teaching-policy enforcement in tutor turns, real citations in place of made-up ones, qe_m02 and qe_m07–m10 rules, OpenRouter cost tracing, and the D-5 supervisor-model pick. |
| **Lakshya (Lead)**, with Claude Code | The original graph and planner, the checkpointer and resume, the approval graph, the c0/c1/c2 arms, the playbook file and the E1/E3 runs. Of 40 commits to `app.py`, 28 are the Lead's and 12 are Poonam's. |

## How it works

- **The planner is code, not a model.** It matches the learner's flagged misconceptions and the message keywords to one route.
- **Resume:** each `tutor ask` is a new process that continues from the SQLite checkpointer. That is the stop-and-resume demonstration.
- **Replan:** a wrong quiz answer on `qe04` contradicts the plan, and the plan moves to v2.
- **Self-correction:** the output guard retries a failing draft once, then uses a safe fallback.

## Likely questions

- **Did the team of agents beat the single agent?** No. In E1, c2, c1 and c0 each scored a 2/48 success proxy with diagnosis recall 0.042, at the same cost. Diagnosis is the bottleneck, not the number of agents.
- **Why is the supervisor code?** It is predictable and testable, and the guide's rule is that the model proposes while code decides.
- **What did the lessons do?** In the development E3 run there was no difference from C2.
- **What is C2-1?** The "Check my step" box confirms a correct substitution, so it can act as an answer check. It is open for the team.

**Files to open:** `src/tutor/app.py`, `Docs/report/ARCHITECTURE.md`, `Docs/report/walkthrough_trace.txt`, `Docs/m3/R3_C2_STEP_FEEDBACK_REVIEW.md`.
