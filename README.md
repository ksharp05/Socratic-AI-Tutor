# Socratic AI Tutor

> Learning through questions, reasoning, and discovery.

> [!IMPORTANT]
> **A first proof of concept now runs end to end:** [run it in 5 minutes](Docs/poc/README.md), with no Docker and no API key.
>
> **What each role delivers, and by when:** [Lead roadmap](Docs/LEAD_ROADMAP.md). **How we work in parallel:** [CONTRIBUTING.md](CONTRIBUTING.md).

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

**Building.** Every box of the architecture exists in a basic form. Each role now replaces the stand-in in its own box with the real version.

| Document | What it covers | Status |
|---|---|---|
| [Socratic Tutor — Agentic AI Architecture Guide](Docs/Socratic%20Tutor%20%E2%80%94%20Agentic%20AI%20Architecture%20Guide.pdf) (Poonam, 19 Oct) | The architecture, the six team roles, the hand-offs between them, and who owns which folder | Reference |
| [Project plan](Docs/plan/README.md) (24 Oct) | Builds on the guide with a dated schedule, design decisions, evaluation design, security and privacy, risks and viva preparation | Proposed |
| [Proof of concept](Docs/poc/README.md) (24 Oct) | One chapter and two misconceptions through every box: guards, planner, specialists, MCP tools with hooks, learner model, teacher approval, traces and a simulated-student smoke test | **Runs; 54 tests pass** |
| [Lead roadmap](Docs/LEAD_ROADMAP.md) (31 Oct) | The team, what we found on 31 Oct, the schedule to the viva, what each role delivers at each milestone, and who owns which file | **Current** (dates confirmed at the 1 Nov meeting) |

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
| R6 Deployment and operations | Shivam or Sharath (to confirm) |
| R5b Evaluation engineer (proposed) | The other of Shivam and Sharath |

What each role owns and never does: [Lead roadmap · Team](Docs/LEAD_ROADMAP.md#team).

## Quick start

**Running the browser beta:** see the [beta run guide](Docs/RUN_GUIDE.md) for setup, data access, live and offline modes, and troubleshooting.

**New to the project?** Follow the step-by-step [setup guide](Docs/SETUP.md): access, install, tests, your API key, and troubleshooting for Windows, macOS and Linux. The short version:

```bash
python -m venv .venv
```

Activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS and Linux), then:

```bash
pip install -e ".[dev]"
```

```bash
tutor setup
```

```bash
tutor chat --learner A
```

To use a live model, put your own course key in `.env` and run `tutor check-llm`. The steps are in [Using a real model](Docs/poc/README.md#using-a-real-model); things to try are in the same guide.

**API, web UI and Docker:** run `uvicorn tutor_api.main:app` and `streamlit run ui/app.py`, or `docker compose up --build --wait`. Tokens, endpoints and what is still untested are in the [deployment guide](Docs/deploy/README.md).

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
| `tests/` | Automated tests |
| `Docs/` | The plan, the roadmap, the POC guide, and the contribution and decision logs |

Never committed: `.env`, API keys, NCERT PDFs or page images, the frozen dataset build, held-out data and personal data.
