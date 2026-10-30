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

## Project status

**Building.** Every box of the architecture exists in a basic form. Each role now replaces the stand-in in its own box with the real version.

| Document | What it covers | Status |
|---|---|---|
| [Socratic Tutor — Agentic AI Architecture Guide](Docs/Socratic%20Tutor%20%E2%80%94%20Agentic%20AI%20Architecture%20Guide.pdf) (Poonam, 19 Oct) | The architecture, the six team roles, the hand-offs between them, and who owns which folder | Reference |
| [Project plan](Docs/plan/README.md) (24 Oct) | Builds on the guide with a dated schedule, design decisions, evaluation design, security and privacy, risks and viva preparation | Proposed |
| [Proof of concept](Docs/poc/README.md) (24 Oct) | One chapter and two misconceptions through every box: guards, planner, specialists, MCP tools with hooks, learner model, teacher approval, traces and a simulated-student smoke test | **Runs; 25 tests pass** |
| [Lead roadmap](Docs/LEAD_ROADMAP.md) (30 Oct) | The schedule from 30 Oct, what each role delivers at each milestone, and who owns which file | **Current** |

| Key date | |
|---|---|
| Integration days | Sun 1, Mon 2, Wed 4 and Sun 8 November 2026 |
| Submission | Thursday 12 November 2026, end of day |
| Review, demo and viva | Sunday 15 November 2026 |

## Quick start

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

Things to try, and how to use a real model: [Docs/poc/README.md](Docs/poc/README.md).

## Repository structure

| Path | What it holds |
|---|---|
| `src/tutor/` | The tutor: graphs, agents, MCP servers, hooks, guardrails, learner model |
| `src/tutor_eval/` | Evaluation: the simulated student and the evaluation run |
| `src/socratic_data/` | The dataset's maths kernel, vendored unchanged |
| `content/` | Tutor-visible content: the POC slice and all of dataset v0.10.0's tutor-visible files |
| `eval/` | Evaluation fixtures (development data only) |
| `config/` | `app.toml`: models, thresholds and budgets |
| `tests/` | Automated tests |
| `Docs/` | The plan, the roadmap, the POC guide, and the contribution and decision logs |

Never committed: `.env`, API keys, NCERT PDFs or page images, the frozen dataset build, held-out data and personal data.
