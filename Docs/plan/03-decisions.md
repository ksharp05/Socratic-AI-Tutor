# 03 · Decisions

[← Starting point](02-starting-point.md) · [Plan overview](README.md) · [Next: Architecture →](04-architecture.md)

Every decision here is **proposed** until the team accepts it at kickoff. Once accepted, it is copied into `Docs/DECISIONS.md` with an owner and a date. A later change needs a new entry that says why, citing a `run_id` if an experiment caused it.

## Summary

| ID | Area | Decision |
|---|---|---|
| D1 | Data | Freeze dataset v0.10.0; the application uses copies |
| D2 | Environments | A separate application environment; the dataset package is imported only by `math-tools` and the evaluation service |
| D3 | Repository | One monorepo; pull requests with review; `CODEOWNERS` |
| D4 | Orchestration | A supervisor graph we build ourselves; `create_agent` specialists; Postgres checkpointer and store |
| D5 | Tools | FastMCP 4.1 servers with LangChain's built-in MCP adapter |
| D6 | Tool names | Follow the dataset's security and benchmark contracts |
| D7 | Hooks | LangChain middleware: `wrap_tool_call`, call limits, PII scrubbing |
| D8 | Approvals | A separate, long-lived graph thread for each question set; approval tokens tied to the payload hash |
| D9 | Models | gpt-4.1 supervisor, gpt-4.1-mini specialists, Gemini judge, Llama simulator, Llama Guard 4 |
| D10 | Retrieval | Chroma + bm25s + RRF + cross-encoder reranker + query rewriting |
| D11 | Ingestion | Choose Docling or PyMuPDF by a bake-off on three pages |
| D12 | Copyright | NCERT text never enters git; formulas are quoted only from our own cards |
| D13 | Serving | FastAPI with native SSE; Streamlit UI; role from a signed token |
| D14 | Observability | Postgres trace table, Prometheus, Grafana; Langfuse optional |
| D15 | CI | A deterministic evaluation gate and a compose smoke test; live LLM evaluation on demand only |
| D16 | Learner model | Bayesian Knowledge Tracing plus outer-fringe planning; code decides |
| D17 | Simulated students | Code owns each student's state; the LLM only voices the dialogue |
| D18 | Demo scenarios | `qe_m04` for the main demo; `tr_m08` for the two-learner demo |
| D19 | Independence | R5 freezes the held-out sets and writes new attacks; R3 and R4 are kept apart from them |
| D20 | Pre-registration | Metrics, rules, configurations and run counts are fixed before any held-out run |

---

### D1 · Freeze dataset v0.10.0; the application uses copies

- **Decision.** Copy the files the tutor may see to `data/runtime/`, and the evaluation-only files to `eval/private/`. `data/MANIFEST.json` records each file's SHA-256 and the dataset payload hash (`49862eea…`).
- **Why.** The data side already exceeds the guide's counts (610 benchmark cases against 60; 42 queries against 30). The marks that remain come from the running system.
- **Rejected.** Building more dataset versions in parallel with the application.

### D2 · Separate environments

- **Decision.**
  - Local development uses its own `uv` environment, and the Docker images pin their own lock file.
  - The dataset package `socratic_data` is imported **only** inside the `math-tools` and evaluation containers.
- **Why.**
  - The dataset's environment is hash-locked for reproducibility.
  - `socratic_data` contains the question generator, which must stay out of any process the LLM can see.
- **Rejected.** One shared environment.

### D3 · One monorepo, with review

- **Decision.**
  - This repository holds the application, the evaluation harness, infrastructure and documentation.
  - `main` is protected, and every change arrives through a pull request with one review.
  - `CODEOWNERS` gives R5 `eval/private/` and `eval/attacks/`, and gives R4 `tutor/guardrails/`.
- **Why.** One place to look, enforced separation of roles, and a clean history for the contribution log.

### D4 · Orchestration

- **Decision.**
  - The supervisor and study planner is a LangGraph `StateGraph` we write ourselves.
  - Each specialist is a `create_agent` sub-agent called from a graph node, so its state stays visible through `get_state(subgraphs=True)`.
  - `AsyncPostgresSaver` is the checkpointer, and `AsyncPostgresStore` is the long-term store for learner memory and the playbook.
- **Rejected:**
  - `langgraph-supervisor`, which is archived.
  - `create_react_agent`, which is deprecated.
  - SQLite, because several containers write at the same time.

### D5 · Tools: FastMCP 4.1 with LangChain's MCP adapter

- **Decision.**
  - Four FastMCP 4.1 servers, using streamable HTTP inside Docker and stdio during development.
  - Agents load them through `langchain.mcp.MCPAdapter`, one adapter per server.
  - If the beta adapter fails the day-one spike, use a hand-written adapter of about 60 lines that turns `fastmcp.Client.list_tools()` into LangChain tools. The L7 lab did this conversion by hand.
- **Rejected.** `langchain-mcp-adapters`, which is archived and incompatible with MCP SDK 2.x. The deviation from the guide is recorded.

### D6 · Tool names follow the dataset contracts

- **Decision.**
  - Each server exposes both the security-contract names and the benchmark aliases, so the existing scorers work unchanged.
  - The `study_planner` role in those contracts maps to our supervisor and planner node.
- **Why.** We reuse 670 frozen contracts without writing adapters.

### D7 · Hooks as middleware

- **Decision.**
  - The pre-tool and post-tool hooks are one `wrap_tool_call` middleware shared by every agent.
  - Budgets use `ToolCallLimitMiddleware` and `ModelCallLimitMiddleware`, plus a dollar cap computed from OpenRouter's `usage.cost`.
  - PII scrubbing is a `before_model` hook using Presidio and regular expressions.
- **Why.** These are documented, tested extension points, and every agent gets the same enforcement.

### D8 · Approvals on their own long-lived thread

- **Decision.**
  - Publishing a question set runs on its own graph thread: propose, then validate, then `approve_gate` (`interrupt`), then publish.
  - The thread waits in Postgres, so the teacher can resume it from the dashboard days later with `Command(resume=decision)`.
  - The approval token is an HMAC over the payload's SHA-256.
- **Why.** A teacher approves on their own schedule, not inside a student's session. Tying the token to the hash means any edit invalidates the old approval.

### D9 · Models

All models were checked live on OpenRouter on 24 Oct 2026. Prices are per million tokens, input / output.

| Role | Model | Price | Why |
|---|---|---|---|
| Supervisor, planner, reflection | `openai/gpt-4.1` | $2.00 / $8.00 | The guide asks for a stronger coordinator, and the L11 lab found mini models unreliable in that role |
| Specialists (all four) | `openai/gpt-4.1-mini` | $0.40 / $1.60 | The course-validated default; supports tools and JSON schema |
| E1 fairness configurations (C0 / C1 / C2) | `openai/gpt-4.1-mini` for every role | — | The guide requires the same model across all three |
| Judge | `google/gemini-3.1-flash-lite` | $0.25 / $1.50 | A different family from both the tutor (OpenAI) and the simulator (Meta); also the guide's own example |
| Simulated students | `meta-llama/llama-3.3-70b-instruct` | $0.10 / $0.32 | A third model family, which lowers the risk of collusion; needs no tools |
| Safety classifier | `meta-llama/llama-guard-4-12b` | $0.18 / $0.18 | The guide's default. It supports no tools or `response_format`, so we parse its text output |
| Injection classifier | `meta-llama/Llama-Prompt-Guard-2-86M` (local CPU) | free | The guide's default. Gated on Hugging Face |
| Embeddings, reranker | `BAAI/bge-small-en-v1.5`, `Xenova/ms-marco-MiniLM-L-6-v2` via fastembed (ONNX) | free | Runs on CPU with no torch in the app image. Our scope is English, so multilingual models are unnecessary |

**Client.** `langchain_openrouter.ChatOpenRouter`, with `openrouter_provider={"require_parameters": True, "data_collection": "deny"}`.

**Keys.** We use the API keys provided by the faculty. Spike S6 confirms that the keys can reach each model above. Any substitute comes from the same family and is recorded in `Docs/DECISIONS.md`.

**Cost tracking.** Every response carries `usage.cost`; we log it to traces and to Prometheus, because the course guide asks for cost per case.

### D10 · Retrieval

- **Decision.**
  - A Chroma server, BM25 via bm25s, and Reciprocal Rank Fusion with k = 60. The cross-encoder then reranks the top 20 down to the top 5.
  - Queries are rewritten into textbook vocabulary.
  - Hooks inject the class, chapter and kind filters.
  - There are two collections: `cards` (trusted and committed) and `textbook` (built locally from NCERT PDFs downloaded at first start).

### D11 · Ingestion tool chosen by a bake-off

- **Decision.**
  - On Thu 29 Oct, run Docling (MIT licence, formula-to-LaTeX) and PyMuPDF 2.0 (AGPL licence, fast) on three equation-heavy pages, and pick the one with better equation fidelity by eye.
  - Ingestion runs in a one-shot container built on a CPU-only torch image, which it shares with the guard service.

### D12 · NCERT text never enters git

- **Decision.**
  - The PDFs and the chunks derived from them live in a Docker volume.
  - **Formulas are quoted only from our cards**, which are our own writing and already checked.
- **Why.** The NCERT PDFs say "All rights reserved", and the guide forbids redistributing them.

### D13 · Serving

- **Decision.**
  - FastAPI with native server-sent events.
  - A Streamlit UI with pages chosen by role, and an SSE client built on `httpx-sse`.
  - Demo accounts with signed session tokens. **A user's role always comes from the token, never from chat text.**
- **Rejected:**
  - Chainlit, which has been community-maintained since May 2025.
  - Gradio, which is weaker for a multi-page dashboard.

### D14 · Observability

- **Decision.**
  - **Traces:** a Postgres table, `trace_events`, is the authoritative record of every LLM call, tool call and guard decision. Hooks and callbacks write it, and personal data is scrubbed first.
  - **Metrics:** Prometheus collects metrics from the API and every MCP server.
  - **Dashboards and alerting:** Grafana dashboards, with Grafana-managed alerting that sends a webhook to the API.
  - **Optional:** Langfuse Cloud (free tier), for synthetic runs only.
- **Rejected.** Self-hosted Langfuse, which needs 16 GB of RAM on its own.

### D15 · CI

- **Decision.** GitHub Actions with `setup-uv`, a cached copy of the Hugging Face models, and two main jobs:
  - **Evaluation gate:** deterministic, and fails below the thresholds in `config/eval_gate.yaml`.
  - **Compose smoke test:** uses a stub LLM, so no secrets are needed.

  An optional `live-eval` workflow, started by hand, runs 10 development cases using a secret.
- **Why.** CI must not depend on paid calls or on secrets in pull requests.

### D16 · Learner model

- **Decision.**
  - Bayesian Knowledge Tracing per concept, with hand-set, documented parameters.
  - Mastery threshold 0.95, with sensitivity checks at 0.90 and 0.98.
  - Misconceptions are tracked as separate flags.
  - The next concept comes from the "outer fringe" of the prerequisite graph.
- **Code decides all of this; the LLM only explains the plan.**
- **Why.** It is transparent and defensible without real student data. The research shows that the threshold matters more than the choice of model.

### D17 · Simulated students: code owns the state

- **Decision.**
  - Code holds each card and its knowledge state, produces wrong answers with "buggy rules", and applies transition rules fixed in advance.
  - The LLM only voices the dialogue, and is given a summary of the card at every turn.
  - R5 writes the simulator's buggy rules under `eval/`. R2/R3 write the diagnostician's detection rules separately under `tutor/`. Neither reads the other's code.
- **Why.** LLM-played students are documented to be over-agreeable and too competent. Separate rule implementations stop the evaluation from grading its own answer key.

### D18 · Demo scenarios

- **Decision.**
  - **Main demo:** the Maths stand-in for the guide's concave-mirror example is misconception `qe_m04`: *"I solved x² = 5x by dividing by x and got x = 5. Why is there another answer?"*
  - **Two-learner demo:** `tr_m08`, *"Is sin 30° bigger in a bigger triangle?"* Learner A has `tr_m08` confirmed; learner B has mastered `tr04`.

### D19 · Independence of the held-out sets and attacks

- **Decision.**
  - On Sun 25 Oct, before any tuning, R5 draws and freezes the held-out golden subset and the held-out students.
  - R5 personally writes at least 10 new attacks, with controls.
  - R3 never reads `eval/private/`, and R4 does not see R5's new attacks before E2.
  - The report discloses that the dataset was generated with AI assistance and frozen by R5.
- **Why.** The guide requires that the person tuning the agent does not write the held-out cases, and that the person building the defences does not write the attacks.

### D20 · Pre-registration

- **Decision.**
  - Metric definitions, transition rules, thresholds, configurations and run counts go into `eval/PREREGISTRATION.md` by Wed 4 Nov, and its hash goes in the experiment log.
  - Any change made after seeing held-out results turns the affected cases into development cases, and the report says so.

---

[← Starting point](02-starting-point.md) · [Plan overview](README.md) · [Next: Architecture →](04-architecture.md)
