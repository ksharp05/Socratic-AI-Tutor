# 02 · Starting point

[← Requirements](01-requirements.md) · [Plan overview](README.md) · [Next: Decisions →](03-decisions.md)

## Dataset v0.10.0: what we reuse

The dataset is **frozen and machine-verified**:
- every one of its 1,379 questions has a key that two calculation routes agree on;
- its full test run passes;
- its build reproduces deterministically.

Its teaching content is an **unapproved development preview**, and 2,469 human review tasks are still pending. The application builds on it and does not change it.

Paths below are relative to `socratic_tutor_dataset_v2/builds/v0.10.0/`.

| Asset | What matters for the build | Used by |
|---|---|---|
| `development_preview/practice_questions.jsonl` (665) | Each record has a typed `problem{task_type, givens, concept_ids}`, an `answer_contract`, 3 hint stages, a `mode_policy`, supporting passages, a provisional difficulty and a chapter.<br/>**There is no answer key in the record.**<br/>Every item has `full_worked_solution_visible: false` and `answer_key_visibility: "grading_service_only"`.<br/>The givens are enough for any LLM to solve the item, so they must never reach a quiz context. | Question setter (via `question-bank`), `math-tools` |
| `development_preview/corpus.jsonl` (25 cards) | One short teaching card per concept (`normalized:qe01` … `tr09`, averaging 137 characters), each with a hint, a diagnostic probe and an NCERT anchor (URL, page, section, SHA-256).<br/>Our own writing, not a PDF transcription. | `textbook-kb` (the `cards` collection) |
| `metadata/concepts.jsonl` (25) | An acyclic prerequisite graph (for example, `qe04` depends on `qe02` and `qe03`). `mastery_criterion` is a proposal, not an update rule. | Study planner |
| `metadata/misconceptions.jsonl` (30) | `qe_m01–10`, `ap_m01–10`, `tr_m01–10`, each with an incorrect rule, example wrong work, correct reasoning, a diagnostic probe, distinguishing evidence and a 2-step hint ladder. | Diagnostician, tutor |
| `socratic_data.tasks` | `primary_answer(problem)` computes the typed key; `oracle_answer(problem)` computes it a second way; `render_prompt(problem)`. All 665 practice items verified in 1.6 s. | `math-tools` |
| `socratic_data.math_kernel` | `grade_mathematics(response, expected)` returns `{status, correct, scorable, reason}`, where status is `correct`, `incorrect`, `invalid_response` or `unverified`.<br/>`equivalent(a, b)` and `answers_equivalent(t1, t2)`.<br/>Needs only SymPy. | `math-tools`, grader, leak detector |
| `private/cases.jsonl` (1,379) | Keys plus split and usage:<br/>• practice: 665<br/>• quiz pre-test: 52<br/>• quiz post-test: 52<br/>• development benchmark: 160<br/>• held-out benchmark candidates: 450 | Golden set, quizzes |
| `private/benchmark_*` (610 contracts, tasks, tool contracts) | Scored by `python -m socratic_data.cli score-benchmark`.<br/>The run manifest records the model ID, prompt and playbook hashes, seed and temperature.<br/>Retrieved text must match the frozen card text exactly. | Golden-set runs |
| `private/simulated_students.jsonl` (40) | Split: `development` 16 / `candidate_final` 24.<br/>Each hidden card has 1–2 seeded misconceptions, target concepts, a true mastery for all 25 concepts, and a persona (communication style, confidence, pace). | Simulated-student engine |
| `private/quiz_pairs.jsonl` (52) and `student_quiz_assignments.jsonl` (40) | Matched pre/post forms (22 development / 30 final). Each student is assigned 3 pairs covering their targets. | Pre/post quizzes |
| `private/diagnostics.jsonl` (30) | One probe per misconception, with the wrong response it predicts | Simulator validation, diagnostician tests |
| `private/simulator_policy.json` | Draft rules: at most 8 tutor turns; the outcome is the solver-checked pre/post quiz score; model, prompt, turns and seed are held fixed across comparisons | Harness |
| `private/retrieval_judgments.jsonl` (42 queries) | 25 graded judgments per query, **against the cards only** (15 development / 27 held-out).<br/>Scored by `retrieval_data.summarize_rankings(queries, records, k=5)`. | CI retrieval gate |
| `private/attacks.jsonl` + `clean_controls.jsonl` (30 + 30) and 60 security contracts | Channels: user message 25, homework 2, retrieved passage 2, tool result 1.<br/>Required tool names: `textbook-kb.search`, `math-tools.check_equivalence`, `learner-store.read_learner/update_mastery/update_profile`, `question-bank.propose_set/publish_approved_set`, `control.handoff`.<br/>Agent roles: `study_planner`, `diagnostician`, `tutor`, `grader`, `question_setter`. | E2 |
| `private/rubric.json` (draft) | Ordinal 0–2 dimensions: mathematical correctness, grounding, misconception handling, hint usefulness, learner adaptation.<br/>Binary dimensions: answer leak, mode violation, unsupported citation. | Judge rubric |
| `private/dialogue_fixtures.jsonl` (20) and `human_label_slots.jsonl` (20, empty) | Authored dialogues, each with an expected issue | Detector tests; judge warm-up (not calibration evidence) |
| `metadata/sources.json` | NCERT `jemh104/105/108.pdf` and exemplar `jeep204/205/208.pdf` (Reprint 2026-27), with SHA-256 hashes | The ingest job downloads and verifies these |

> [!WARNING]
> **Grading traps in the maths kernel. The answer adapter must handle these:**
> - Trig arguments are in **radians**, so `sin(30)` ≠ 1/2.
> - A JSON float `0.5` is invalid, but the string `"0.5"` is fine.
> - A scalar answer to a set question is graded *incorrect*, not invalid.
> - `km/hr` is rejected, but `kmph` is accepted.
> - **There is no free-text input adapter.**

## Gaps the application must fill

1. **No textbook section index.** The raw PDF extraction is quarantined. → [Ingestion and retrieval](04-architecture.md#ingestion-and-retrieval)
2. **No approved items and no approval workflow.** The production export is empty. → [Approval gate](04-architecture.md#approval-gate)
3. **No free-text answer adapter** (LaTeX, `sin 30°`, `x = 0 or 5`, unit variants). → [Answers and diagnosis](04-architecture.md#answers-and-diagnosis)
4. **No runtime learner-state schema and no mastery-update rule.** → [Learner model](04-architecture.md#learner-model-memory-and-planner)
5. **No MCP implementations.** The benchmark and security tool names differ. → [MCP tools](04-architecture.md#mcp-tools)
6. **No mapping from a wrong answer to its misconception** for the 665 practice items. → [Answers and diagnosis](04-architecture.md#answers-and-diagnosis)
7. **No simulator runner, quiz-experiment runner or trusted recorders.** → [Simulated students](05-evaluation.md#simulated-students)
8. **No filled lesson schema, and nowhere to store review decisions.** → [Reflexion and playbook](05-evaluation.md#reflexion-and-playbook)
9. **No command-line interface for the retrieval and security scorers.** → [Code checkers](05-evaluation.md#code-checkers)
10. **No policy for what the tutor reveals after the last hint.** → [Guardrails](04-architecture.md#guardrails)
11. **Human review and independent authorship are still pending.** → [Human-only tasks](07-team-and-roles.md#human-only-tasks)

## Reusable code from HW2 and the labs

Our HW2 support agent (Lectures 4–8) has pieces worth reusing. Copy them from the member who wrote them and record the reuse in the contribution log.

| HW2 piece | What it does | Change for the tutor |
|---|---|---|
| `llm.py` | OpenRouter client with disk cache, retry and JSON mode | Count `ChatOpenAI` usage too; make the counters thread-safe; export to Prometheus |
| `retrieval.py` | `rrf`, `hybrid`, `postprocess`, and a tokenizer that keeps codes intact | Maths-aware tokenizer; add the reranker; add Chroma metadata filters |
| `kb.py` | Heading-aware splitter | Split on NCERT section, example and exercise boundaries |
| `evalkit/metrics.py`, `scripts/evaluate_dev.py` | Deterministic weighted scorer with a retrieval-only mode | Tutor metrics; the retrieval-only mode suits a free CI job |
| `scripts/run_batch.py` | Threaded batch runs with `--resume` | New trace fields |
| `policy.py` | `detect_injection`, `wrap_untrusted` | Reuse as one guardrail layer |
| `tests/test_human_approval.py` | No-LLM approval tests | Adapt for the approval gate |

**HW2 weaknesses not to repeat:**
- A regex "triage" did most of the work, rather than the model's tool choices.
- The verifier never retried.
- Token counts were wrong under threads.
- The reranker and query rewriting were never implemented.

**Patterns from the course labs:**
- `ChatOpenAI(base_url="https://openrouter.ai/api/v1")`.
- L7: `MCPServer`, the MCP SDK 2.0 name for the old FastMCP class.
- L8: `StateGraph`, a checkpointer, `interrupt_before`, time travel.
- L12: a supervisor using `with_structured_output(Route, method="json_schema", strict=True)`, and a usage meter that reads `usage_metadata`.

No lab covered a long-term store, `interrupt()`/`Command`, judge calibration, guardrails or deployment, so those need extra care.

## What changed since the course guide

Checked against PyPI, OpenRouter and official documentation on 24 Oct 2026.

| Finding | Consequence |
|---|---|
| `langchain-mcp-adapters` 0.3.2 was **archived on 17 Sep 2026**. It needs `mcp<2`; FastMCP 4.1.3 needs `mcp>=2.2`, so the two cannot be installed together. LangChain 1.4.7 ships MCP support as the `langchain[mcp]` extra. | Use FastMCP 4.1 servers with `langchain.mcp.MCPAdapter`. A day-one spike tests this; the fallback is a hand-written adapter of about 60 lines. |
| `create_react_agent` is deprecated, and `langgraph-supervisor` is archived. | Specialists use `langchain.agents.create_agent`. The supervisor is a `StateGraph` we build ourselves. |
| LangChain 1.x middleware (`wrap_tool_call`, tool-call and model-call limits, PII, summarisation) maps directly onto the guide's pre- and post-tool hooks. | The hooks are written as shared middleware. |
| The 42 retrieval labels cover only the 25 short cards, and the scorer rejects any other passage. | Those labels become a CI gate. A **new section-level labelled set** over the real textbook index provides the main retrieval evidence. |
| Studies from 2025–26 find that LLM-simulated students are over-agreeable, too competent, and drift out of character. | Code owns each student's state and quiz answers; the LLM only voices the dialogue. |
| Self-hosting Langfuse v4 needs six containers and 16 GiB of RAM. Docker Desktop's WSL2 gets half the host's RAM by default. | Traces go to a Postgres table; Langfuse Cloud is optional. |
| Four MCP servers, the API and the evaluation runner write state at the same time. | **Postgres** for the checkpointer, the store and the app tables. |
| OpenAI retires gpt-4.1, gpt-4.1-mini and gpt-4o-mini on 14 Jan 2027. | That is after our viva, so it has no impact. Record the exact model IDs. |

### Package versions (PyPI, 24 Oct 2026)

| Package | Version | Note |
|---|---|---|
| langgraph | 1.2.17 | `interrupt(..., response_schema=)` needs ≥ 1.2.12 |
| langchain | 1.4.7 | The `[mcp]` extra pulls `fastmcp>=4.0.11,<5` |
| langgraph-checkpoint-postgres | 3.2.0 | `AsyncPostgresSaver`, `AsyncPostgresStore` |
| fastmcp | 4.1.3 | Needs `mcp>=2.2,<3` |
| mcp | 2.3.0 | `mcp.server.fastmcp` removed; the class is renamed `MCPServer` |
| langchain-openrouter | 0.2.9 | `ChatOpenRouter`, with provider routing and `json_schema` output |
| fastapi | 0.162.0 | Native server-sent events since 0.135 |
| streamlit | 1.66.1 | `st.navigation` pages by role; `st.write_stream` |
| chromadb / chromadb-client | 1.5.9 | Server image `chromadb/chroma`, with data at `/data` |
| bm25s | 0.3.15 | Fast BM25 that can save and load its index |
| fastembed | 0.9.0 | ONNX embeddings and reranking, without torch |
| docling | 2.142.1 | MIT licence; converts formulas to LaTeX |
| pymupdf | 2.0 | AGPL licence; `pymupdf4llm` is merged into it |
| presidio-analyzer | 2.2.364 | Recognisers for Indian ID numbers |
| prometheus-client | 0.26.0 | `make_asgi_app()` mount |
| langfuse (SDK) | 5.0.4 | v4 server is current |

## Setup each member needs

- [ ] Git and a GitHub account with access to the team repository.
- [ ] Python 3.12 and [uv](https://docs.astral.sh/uv/).
- [ ] Docker Desktop, with at least 8 GB of memory for WSL2 (set in `%UserProfile%\.wslconfig` on Windows).
- [ ] The team OpenRouter key in your local `.env`. Never commit it.
- [ ] Access to `meta-llama/Llama-Prompt-Guard-2-86M` on Hugging Face, plus a read token in `.env`.

---

[← Requirements](01-requirements.md) · [Plan overview](README.md) · [Next: Decisions →](03-decisions.md)
