# R6 · Deployment and operations engineer · Sharath S Nadig (from 13 Nov)

**What the guide asks** (lectures L13 and L16):
- FastAPI with streaming;
- `docker compose up` starting the app, the MCP servers, Prometheus and Grafana;
- prompts and model IDs in one versioned config;
- an evaluation run in CI that fails below a threshold;
- one working alert, an install on a clean machine, and one failed CI run with an explanation.

## What exists

| Piece | Where |
|---|---|
| FastAPI service with a streaming chat endpoint (server-sent events); role and learner taken from the bearer token | `src/tutor_api/main.py` |
| Streamlit UI that talks only to the API | `ui/app.py` |
| `docker compose up --build --wait`; the `ops` profile adds Prometheus and a provisioned Grafana dashboard | `docker-compose.yml`, `ops/` |
| **Answer-leak alert: Grafana rule, webhook, teacher alerts, run evidence** | `ops/`, `src/tutor_api/`, `Docs/deploy/README.md` |
| Versioned config (models, retrieval, budgets) | `config/app.toml` |
| CI: portable tests, registry check, two harness gates, front-door gate, security gate | `.github/workflows/ci.yml` |
| A real CI failure and its fix | `Docs/ci_failure.md` |
| Fresh-clone install (5 Nov), with state kept across a restart | `Docs/m2/FRESH_INSTALL.md` |
| Live beta on Vercel and Neon Postgres: consent, spend ledger, hosted lease (200 requests or USD 0.50) | `Docs/deploy/VERCEL_BETA.md`, `vercel.json` |
| Latency review of the beta | `Docs/report/beta-latency/` |

## Who built it

| Built by | What |
|---|---|
| **Poonam, standing in as R6** (11 Nov) | The answer-leak alert: the API part and the Grafana part (provisioned rule, webhook, Compose token). She ran the `ops` profile and confirmed that the alert fired and reached the teacher's page. She also filled R6's part of report section 2. |
| **Lakshya (Lead)**, with Claude Code | The FastAPI service, the UI, Docker Compose, CI and its gates, the config, the fresh-clone check, and the whole Vercel and Neon beta, including every production deploy. |
| **Sharath** (confirmed as R6 on 13 Nov) | No work is recorded in the log or in git yet. **Confirm with Sharath** what he has done, such as the E5 clean-machine install or a mobile check, and add it to the log if so. |

## How it works

- **Production:** `socratic-tutor-beta` on Vercel runs Beta `db49b7d` (`dpl_9uoVZqt…`). The provider key is a write-only "sensitive" variable.
- **Spending:** a Postgres row-locked ledger is shared by every instance, so the site can't overspend under load.
- **CI** runs on every PR and on pushes to `main` and `Beta`. Any regression against the front-door baseline fails the build.

## Likely questions

- **Show one command bringing it up.** `docker compose up --build --wait`, then `--profile ops` for Prometheus and Grafana on port 3000.
- **Show a failed CI run.** `Docs/ci_failure.md` explains what failed and the fix.
- **What does the alert watch?** Answer leaks blocked by the output guard. It fires to Grafana and the teacher's page.
- **Where is streaming?** `chat_stream` in `src/tutor_api/main.py` returns server-sent events (`text/event-stream`).
- **What is not done?** The mobile check on students' phones.

**Files to open:** `docker-compose.yml`, `.github/workflows/ci.yml`, `Docs/deploy/README.md`, `Docs/deploy/VERCEL_BETA.md`, `Docs/ci_failure.md`.
