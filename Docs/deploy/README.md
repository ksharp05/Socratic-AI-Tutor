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

**Production:** set `TUTOR_ENV=production`, and the API refuses to start without `TUTOR_API_TOKENS`. It never falls back to the public development tokens above. Use long random tokens, keep them in `.env`, and never commit them.

## Endpoints

| Method and path | Who | What |
|---|---|---|
| `GET /health` | anyone | `{"status": "ok", "llm": ...}` |
| `GET /metrics` | anyone (scraped by Prometheus) | Prometheus text format |
| `POST /alerts/grafana` | Grafana, with `TUTOR_ALERT_TOKEN` as its bearer token | Grafana's webhook body. Stores each alert for teachers. Returns 404 when `TUTOR_ALERT_TOKEN` is unset; refuses the public default `dev-grafana-alerts` when `TUTOR_ENV=production` |
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
| `GET /teacher/alerts` | teacher | System alerts from Grafana, newest first (at most 50) |
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
| `tutor_output_guard_checks_total` | none (every draft the output guard checked) |
| `tutor_alerts_received_total` | `status` (`firing`, `resolved`) |

**How the counts are collected.** Tool calls, denials and blocked leaks are read from the `trace_events` rows that the ToolBus hooks and the output guard already write. The counts therefore match `tutor trace`.

## Answer-leak alert

Grafana loads the rule from `ops/grafana/provisioning/alerting/leak_alert.yml`. It fires when more than 5% of the drafts the output guard checked in the last 10 minutes were blocked as answer leaks, for 2 minutes in a row. Grafana then posts to `POST /alerts/grafana`, and teachers see it under **System alerts** on the Learners page and in `GET /teacher/alerts`.

- **Token.** Compose gives Grafana and the API the same `TUTOR_ALERT_TOKEN`. Its default, `dev-grafana-alerts`, is public, so set your own outside development; with `TUTOR_ENV=production` the API refuses the default.
- **Fire it for the demo.** With the `ops` stack running:
  ```bash
  docker compose exec -T api python - < scripts/fire_leak_alert.py
  ```
  A deliberately leaky stand-in for the model answers 20 questions. The output guard blocks every leaky draft, so no student sees one, and no live model is called. The alert turns to Firing in Grafana (Alerting → Alert rules) after about 3 minutes.
- **Port 8000 busy?** Start the stack with `TUTOR_API_PORT=18000 docker compose --profile ops up --build --wait` and use `http://localhost:18000`.
- **Evidence, 11 November 2026:** [the rule firing](leak_alert/1_alert_rule_firing.webp), [the dashboard after the fire script](leak_alert/2_dashboard_leaks_blocked.webp) and [the teacher's System alerts](leak_alert/3_teacher_system_alerts.webp).

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

- **Docker.** When this was written, Docker was not installed and the files were never built. On 5 November 2026 the base stack was built and run from a fresh clone and kept its state across a restart; see [Milestone 2 install evidence](../m2/FRESH_INSTALL.md#compose-acceptance-after-restart---5-november-2026). The `ops` profile was run on 11 November 2026 (next item).
- **Prometheus and Grafana.** Run by Poonam (R3) on 11 November 2026 on macOS 26.5 with Docker 29.5.3, the stub model and `TUTOR_API_PORT=18000`. All four services were healthy; Prometheus scraped the API, and Grafana loaded the dashboard, the leak alert rule and the webhook contact point. After `scripts/fire_leak_alert.py`, 20 of 40 checked drafts were blocked as leaks. The rule went from Pending to Firing (value 0.5), Grafana posted to `POST /alerts/grafana`, and the alert appeared under **System alerts** on the teacher's Learners page. A student token got 403 from `GET /teacher/alerts`. Not checked yet: the alert resolving, and the panels fed by chat turns, because the fire script bypasses the chat API.
- **The UI.** It was checked headlessly with Streamlit's `AppTest` against a local API: a student chat turn over SSE and a teacher proposal. It has not been clicked through in a browser.
- **Streaming.** The POC graph does not stream model tokens. `/chat/stream` runs the whole turn first, then sends the reply in chunks.
- **Under the plan but not built here:**
  - login with passwords (`POST /auth/login`);
  - Postgres;
  - the `eval` Compose service;
  - concurrent turns.


## Local candidate browser check - 6 November 2026

The updated student chat was checked in an in-app browser against isolated, stub-only local API/UI servers: chapter selection/pinning, AP probe/self-correction, per-turn reference display, new session/chapter switch, and trigonometry chat. Desktop (1280px) and mobile (390px) checks showed no horizontal overflow. Five new real API/AppTest learner checks also cover stream failures and restoring a saved reply without replay. This is assistant-operated development acceptance, not an independent member installation or human teaching review. See `Docs/product_quality/v1/CURRENT_CHECKPOINT.json`; temporary test servers were stopped.
