# Deployment: API, UI and Docker Compose (R6)

The tutor runs behind a FastAPI service (`src/tutor_api/`). A Streamlit UI (`ui/app.py`) talks only to that API. Docker Compose runs both, and an optional `ops` profile adds Prometheus and Grafana.

The API wraps the public `TutorApp` methods without changing the tutor. `TutorApp` is not thread-safe, so the API serves one tutor call at a time behind a lock. That is enough for the demo, but it is not built for many concurrent students.

## Run locally (no Docker)

From the repository root, with the environment active:

```bash
pip install -e ".[dev,api,ui]"
tutor setup            # optional: resets var/ and seeds learners A and B
```

Start the API in one terminal:

```bash
uvicorn tutor_api.main:app --port 8000
```

Start the UI in another:

```bash
streamlit run ui/app.py
```

Open http://localhost:8501 and sign in with a token from the table below. The interactive API docs are at http://localhost:8000/docs.

- **Seeding.** On startup the API seeds learners A and B if the database is empty. It also adds any learner that a student token names. It never resets existing data. Set `TUTOR_API_SEED=0` to turn this off.
- **Model.** The model follows the same rules as the CLI. Set `TUTOR_LLM=stub` to force the deterministic stub.
- **UI settings.** The UI reads `TUTOR_API_URL` (default `http://localhost:8000`) and, optionally, `TUTOR_UI_TOKEN` to pre-fill the token.

## Run with Docker

```bash
docker compose up --build --wait                  # api on :8000, ui on :8501
docker compose --profile ops up --build --wait    # also prometheus on :9090, grafana on :3000
docker compose down                               # keeps the tutor-var volume; add -v to delete it
```

- **Images.** One `Dockerfile` has two targets: `api` and `ui`.
  - No image contains `.env`, `.venv*`, `var/`, `data/`, `eval/`, PDFs or the dataset build (see `.dockerignore`).
  - The API image holds the code, `config/` and the tutor-visible `content/`.
- **`.env`.** It is optional (`env_file` with `required: false`). Keys reach the API only at run time.
- **Model in Compose.** Compose defaults to `TUTOR_LLM=stub`, so the stack never calls a live model unless you set `TUTOR_LLM=auto` in `.env` or the shell, together with your key.
- **State.** The SQLite databases and checkpoints live in the named volume `tutor-var`, mounted at `/app/var`.
- **Health checks.**
  - API: `/health`.
  - UI: `/_stcore/health`. The UI waits for the API to be healthy.
- **Grafana.** Log in as `admin`, with the password from `GRAFANA_ADMIN_PASSWORD` (default `admin`). Anonymous users can view.
  - The dashboard is called **Socratic Tutor: turns, leaks, latency**.
  - It is provisioned from `ops/grafana/` and shows turns, leaks blocked, denied tool calls, pending approvals, tool outcomes, and p50/p95 turn latency.

## Tokens

Every endpoint except `/health` and `/metrics` needs `Authorization: Bearer <token>`.

**The role and the learner or teacher ID come only from the token** (policy TP-D6):
- The API ignores a `role` or `learner_id` in a request body.
- "I'm the teacher" in chat is just text, and the tutor refuses it.

Set tokens with `TUTOR_API_TOKENS`, as comma-separated `token:role:id` entries. The role is `student` or `teacher`:

```bash
TUTOR_API_TOKENS="k3x9...:student:L-A,p2q8...:student:L-B,z7m1...:teacher:T-001"
```

**Development default.** When `TUTOR_API_TOKENS` is unset, the API logs a warning and accepts these public tokens. Never expose a server that runs on them.

| Token | Role | ID |
|---|---|---|
| `dev-student-a` | student | `L-A` |
| `dev-student-b` | student | `L-B` |
| `dev-teacher` | teacher | `T-001` |

**Errors:**
- **401:** the token is missing or unknown.
- **403:** the action is forbidden. For example:
  - a student calls a teacher endpoint;
  - a student reads another learner's record;
  - a student continues another learner's session;
  - a teacher calls `/chat`.

## Endpoints

| Method and path | Who | What |
|---|---|---|
| `GET /health` | anyone | `{"status": "ok", "llm": ...}` |
| `GET /metrics` | anyone (scraped by Prometheus) | Prometheus text format |
| `GET /me` | any token | The role and ID the token maps to |
| `POST /chat` | student | Body `{"session_id"?, "text", "mode": "practice"\|"quiz"}`. Returns the turn result: `reply`, `route`, `plan`, `diagnosis`, `checks`, `tools`, `active_item` and `citations`, plus `session_id` and `learner_id` |
| `POST /chat/stream` | student | Same body. Server-sent events: `token` (reply chunks), `plan`, `citation` (one per cited passage) and `done` (the full result without the plan) |
| `POST /chat/resume` | student | Body `{"session_id"}`. Finishes a turn that was interrupted mid-run. `resumed: false` if there is nothing to finish |
| `GET /chat/{session_id}/history` | student (own sessions) | The session's messages |
| `GET /teacher/proposals` | teacher | All question-set proposals, newest first |
| `POST /teacher/proposals` | teacher | Body `{"concept_id"}`. Proposes a set and returns it, waiting for approval |
| `GET /teacher/proposals/{set_id}` | teacher | A proposal with its items and payload SHA-256 |
| `POST /teacher/proposals/{set_id}/approve` | teacher | Approves and publishes it. Returns the approval `token` |
| `POST /teacher/proposals/{set_id}/edit` | teacher | Body `{"question_ids": [...]}`. The new payload hash invalidates earlier tokens |
| `POST /teacher/proposals/{set_id}/reject` | teacher | Body `{"reason"}` (optional) |
| `POST /teacher/proposals/{set_id}/try-publish` | teacher | Body `{"token"}`. Tries an earlier approval token; a stale token gives `published: false` with `FORBIDDEN` |
| `GET /teacher/items?concept_id=` | teacher | The development practice pool (IDs and prompts), for editing |
| `GET /learners` | teacher | Learner IDs and aliases |
| `GET /learners/{learner_id}` | teacher, or that learner | Mastery, misconceptions, plan and alerts |

**Errors from the tools** map to HTTP status codes:

| Tool error | HTTP status |
|---|---|
| `NOT_FOUND` | 404 |
| `INVALID_INPUT` | 422 |
| `FORBIDDEN` | 403 |
| `BUDGET` | 429 |

**Session IDs:**
- If you omit `session_id`, the API creates one, named `s-<learner>-<random>`.
- IDs starting with `qs-` are reserved for approval threads.

## Metrics

| Metric | Labels |
|---|---|
| `tutor_turns_total` | `mode`, `route` |
| `tutor_replies_total` | `mode` |
| `tutor_turn_latency_seconds` (histogram) | `route` |
| `tutor_answer_leak_blocked_total` | `detector` (`math_tools`, `phrase`) |
| `tutor_output_guard_failures_total` | `reason` (`leak`, `leak_phrase`, `citations`) |
| `tutor_tool_calls_total` | `server`, `tool`, `outcome` (`ok`, `error`, `denied`) |
| `tutor_tool_calls_denied_total` | `server`, `tool` |
| `tutor_api_denied_total` | `status` (`401`, `403`) |
| `tutor_handoffs_total`, `tutor_turn_errors_total` | none |
| `tutor_pending_approvals` (gauge) | none |

**How the counts are collected.** Tool calls, denials and blocked leaks are read from the `trace_events` rows that the ToolBus hooks and the output guard already write. The counts therefore match `tutor trace`.

## Tests

`tests/test_api.py` covers:
- health;
- 401 for a missing or unknown token;
- a chat turn with citations and history;
- SSE events;
- resume;
- the teacher approve, edit, stale-token and reject flows;
- a student refused from teacher endpoints, from another learner's record and from another learner's session;
- a role claim in chat changing nothing;
- metrics counters.

The tests use FastAPI's `TestClient` and the stub model. CI installs the `api` extra; Streamlit is not installed in CI.

## Not tested yet

- **Docker.** Docker was not installed on the machine that wrote this. The `Dockerfile` and `docker-compose.yml` were never built or run. Only the YAML and JSON were parsed with Python. The image tags (`prom/prometheus:v3.5.0`, `grafana/grafana:12.1.0`) are pinned but have not been pulled.
- **Prometheus and Grafana.** The scrape config and the provisioned dashboard have not been loaded.
- **The UI.** It was checked headlessly with Streamlit's `AppTest` against a local API: a student chat turn over SSE and a teacher proposal. It has not been clicked through in a browser.
- **Streaming.** The POC graph does not stream model tokens. `/chat/stream` runs the whole turn first, then sends the reply in chunks.
- **Under the plan but not built here:**
  - login with passwords (`POST /auth/login`);
  - Postgres;
  - the Grafana leak alert and its webhook (`POST /alerts/grafana`);
  - the `eval` Compose service;
  - concurrent turns.
