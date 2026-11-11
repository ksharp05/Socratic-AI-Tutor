# Socratic AI Tutor

> Learning through questions, reasoning, and discovery.

> [!IMPORTANT]
> **Course submission, 12 November 2026.** One command starts the tutor: `docker compose up --build --wait` ([Quick start](#quick-start)).
> - Live browser beta: https://socratic-tutor-beta.vercel.app/beta/
> - Evaluation report: [Docs/report/EVALUATION_REPORT.md](Docs/report/EVALUATION_REPORT.md)
> - Release note: [Docs/releases/2026-11-12-v1.0.md](Docs/releases/2026-11-12-v1.0.md)

## Overview

Socratic AI Tutor is a project to build an AI learning companion that helps students develop understanding through guided dialogue. Instead of giving answers straight away, the tutor will ask questions, encourage reflection, and help learners explain their reasoning.

We are building it as Project 3 of the Agentic AI Capstone. It is an NCERT tutor for a Class 10 student and their teacher. It:
- finds what the student misunderstands;
- gives hints grounded in the textbook, without giving away the answer;
- checks work with a solver;
- plans what to practise next from a model of each learner.

**Scope:** Class 10 Maths in English. Chapters: Quadratic Equations, Arithmetic Progressions, and Introduction to Trigonometry.

## Dataset

See the [dataset report](Docs/datasets/DATASET_REPORT.md) and [NCERT source catalogue](Docs/datasets/NCERT_CATALOGUE.md) for current coverage, access, and review limits.

## Project status

**Submitted for the course (v1.0).** Every box of the architecture is built and tested.
- **Tests:** 2,856 automated tests and three CI gates pass on a fresh clone.
- **Evidence:** all results are development evidence, from simulated students, synthetic attacks and independently labelled public data. No real-student or teacher-reviewed result is claimed (see the report's limitations).

| Submission item | Where |
|---|---|
| Evaluation report (problem, system, data, method, results, lessons, limitations, pilot needs) | [Docs/report/EVALUATION_REPORT.md](Docs/report/EVALUATION_REPORT.md) |
| Architecture diagram and numbered walkthrough of a real trace | [Docs/report/ARCHITECTURE.md](Docs/report/ARCHITECTURE.md) |
| Threat model (v3) | [Docs/THREAT_MODEL.md](Docs/THREAT_MODEL.md) |
| Memory policy | [Docs/MEMORY_POLICY.md](Docs/MEMORY_POLICY.md) |
| Experiment log | [Docs/EXPERIMENT_LOG.md](Docs/EXPERIMENT_LOG.md) |
| Contribution log | [Docs/CONTRIBUTIONS.md](Docs/CONTRIBUTIONS.md) |
| Decision log (D-1 to D-7) | [Docs/DECISIONS.md](Docs/DECISIONS.md) |
| Independent public test set (15 free labelled datasets) | [Docs/testing/PUBLIC_TESTSET.md](Docs/testing/PUBLIC_TESTSET.md) |
| Live beta: deployment, consent, spending cap | [Docs/deploy/VERCEL_BETA.md](Docs/deploy/VERCEL_BETA.md) |
| Teaching policy (what counts as giving the answer away) | [Docs/policy/TEACHING_POLICY.md](Docs/policy/TEACHING_POLICY.md) |
| Current state and open items | [Docs/m3/CHECKPOINT.md](Docs/m3/CHECKPOINT.md) |

**History:**
- the [project plan](Docs/plan/README.md), 24 Oct;
- the [proof of concept](Docs/poc/README.md), 24 Oct;
- the [Milestone 2 status](Docs/m2/STATUS.md), 5 Nov;
- the [lead roadmap](Docs/LEAD_ROADMAP.md), 31 Oct.

The course's *Socratic Tutor: Agentic AI Architecture Guide* (PDF) is course material and is not redistributed here.

| Key date | |
|---|---|
| Team meeting | Sunday 1 November 2026 |
| Milestones (proposed) | M1 Mon 2, M2 Wed 4, M3 Fri 6, human day Sat 7, M4 Mon 9 November |
| Content freeze | Wednesday 11 November, 9 pm |
| Submission | Thursday 12 November 2026, end of day (our target: 6 pm) |
| Review, demo and viva | Sunday 15 November 2026 |

## Team

| Role | Name |
|---|---|
| Lead, R1 Domain and product, R5 Evaluation and red team | Lakshya |
| R2 Knowledge and memory | Rizwan |
| R3 Agents and orchestration | Poonam |
| R4 Tools, control and security | Swati |
| R6 Deployment and operations | Poonam, standing in since 11 Nov (Grafana leak alert, beta hint). Shivam or Sharath to confirm |

What each role owns and never does: [Lead roadmap · Team](Docs/LEAD_ROADMAP.md#team).

## Quick start

**Try it without installing anything:** the live beta at https://socratic-tutor-beta.vercel.app/beta/ covers the three chapters. It asks for consent before any model call; your progress is kept per browser, and "Forget my data" deletes it. To run the beta locally, see the [beta run guide](Docs/RUN_GUIDE.md). That needs a separately supplied, authorised textbook index, which a fresh clone does not contain.

**New to the project?** Follow the [setup guide](Docs/SETUP.md) (requirements, Docker or local Python, live key, private data, troubleshooting) or its one-page [install checklist](Docs/INSTALL_CHECKLIST.md). First see what is missing; this check is read-only:

```powershell
powershell -ExecutionPolicy Bypass -File setup\check_prerequisites.ps1   # macOS/Linux: bash setup/check_prerequisites.sh
```

**Route A, Docker** (Docker Desktop; on Windows also WSL 2): run `docker compose up --build --wait`, open http://localhost:8501 and sign in with the development token `dev-student-a` or `dev-teacher`.

**Route B, local Python 3.12:**

```powershell
powershell -ExecutionPolicy Bypass -File setup\install_python_env.ps1   # macOS/Linux: bash setup/install_python_env.sh
.venv\Scripts\Activate.ps1                                               # macOS/Linux: source .venv/bin/activate
pytest -q
tutor setup
tutor chat --learner A
```

The install script creates `.venv`, runs `pip install -e ".[dev,api,ui]" -r requirements-beta-dev.txt` and `pip check`. None of this needs an API key or private data. `pytest -q` runs the 2,266 tests in `tests/`.

The CI command runs every suite (2,856 tests; checked from a fresh clone on 11 Nov):

```powershell
$env:TUTOR_LLM = "stub"; pytest -q --strict-markers -m "not local_corpus" tests tests_beta tests_book_pipeline tests_integration_v02
```

**For a live model,** put your own course key in `.env` (`LLM_API_KEY=`, plus `TUTOR_LLM=auto` for Docker) and run `tutor check-llm` ([setup guide, section 6](Docs/SETUP.md#6-optional-a-live-model-with-your-own-key)). R6's short version: [R6 key guide](Docs/deploy/R6_KEY_GUIDE.md).

**API and web UI without Docker:** `uvicorn tutor_api.main:app` and `streamlit run ui/app.py`. Tokens, endpoints and what is still untested are in the [deployment guide](Docs/deploy/README.md).

## Repository structure

| Path | What it holds |
|---|---|
| `src/tutor/` | The tutor: graphs, agents, MCP servers, hooks, guardrails, learner model |
| `src/tutor_api/`, `ui/` | The HTTP API (FastAPI) and the Streamlit UI |
| `docker-compose.yml`, `Dockerfile`, `ops/` | Containers, plus Prometheus and Grafana (profile `ops`) |
| `src/tutor_eval/` | Evaluation: the simulated student and the evaluation run |
| `src/socratic_data/` | The dataset's maths kernel, vendored unchanged |
| `content/` | Tutor-visible content: the POC slice and all of dataset v0.10.0's tutor-visible files |
| `eval/` | Evaluation fixtures (development data only) |
| `config/` | `app.toml`: models, thresholds and budgets |
| `src/v02_integration/` | Opt-in contextual hints and replies (`TUTOR_CONTEXTUAL_HINTS=1`) |
| `src/socrates_beta/`, `config/beta/` | The browser beta, mounted at `/beta/` when configured (needs private data) |
| `src/ncert_pipeline/`, `tools/` | NCERT extraction and acquisition tools (need private source files) |
| `scripts/` | Milestone probes, smoke runs and the development test-pack runner (`scripts/m2/`) |
| `setup/` | Prerequisite check and Python environment install scripts |
| `tests/`, `tests_beta/`, `tests_book_pipeline/`, `tests_integration_v02/` | Automated tests run by CI. Only tests marked `local_corpus` need private data, and CI skips them |
| `Docs/` | The report, architecture, threat model, memory policy, logs, setup and run guides, deployment guides, and milestone evidence |

Never committed: `.env`, API keys, NCERT PDFs or page images, the frozen dataset build, held-out data and personal data.
