# Lead roadmap · 31 Oct → 15 Nov 2026

The team plan from Saturday 31 October to the viva: who owns what, what to ask each person for and when, and what counts as done. Written by the Lead; everyone works from it.

It re-dates [08 · Schedule](plan/08-schedule.md). **Where the two differ, this roadmap wins.** Everything else in the [plan](plan/README.md) still applies.

**Contents:**
- [Team](#team)
- [Where we are](#where-we-are-sat-31-oct)
- [What we found on 31 Oct](#what-we-found-on-31-oct)
- [Timeline](#timeline)
- [Who owns which file](#who-owns-which-file)

## Team

Proposed in the team group on 31 Oct ([D-2](DECISIONS.md)); confirmed at the meeting on Sun 1 Nov.

| Role | Name | Owns | Never does |
|---|---|---|---|
| **Lead** | Lakshya | This roadmap, integration days, go/no-go, decision log | — |
| **R1** Domain and product | Lakshya, with everyone contributing | Teaching and mode policy, leak definition, misconception and rubric review (with the teacher), demo script, held-out policy check, lesson review, judge labels | Write attacks |
| **R2** Knowledge and memory | Rizwan | NCERT ingestion, hybrid retrieval, learner model and memory, memory policy, diagnosis rules with R3 | — |
| **R3** Agents and orchestration | Poonam | LangGraph graph, prompts, planner, the four specialists, baselines, Reflexion loop, diagnosis rules with R2 | **Open held-out cases, or look at held-out results before the freeze** |
| **R4** Tools, control and security | Swati | The four MCP servers, hooks, guardrails, approval gate, threat model, all refusal and safety wording | **See R5's new attacks before E2** |
| **R5** Evaluation and red team | Lakshya | Held-out sets, new attacks, harness, simulator, pre-registration, experiments, results tables | **Edit prompts, agents, guards or diagnosis rules** |
| **R6** Deployment and operations | Sharath S Nadig (confirmed by the Lead, 13 Nov) | Compose, API, UI, auth, Prometheus and Grafana, alerts, CI, README, demo recording | — |
| **R5b** Evaluation engineer (**proposed**) | Shivam Srivastava (proposed; to confirm) | Judge runner, metrics, cost logging, report tables, the NCERT check set; second judge rater and held-out spot-checker. Builds on development data only; sees held-out cases only for the spot-check | **Edit prompts, agents, guards or diagnosis rules** |

**Why R5b:** six people and Lakshya holds two roles, so one person has no role yet. R5 carries the heaviest load in the last week, and R5b takes the parts that need no held-out access. **Fallback:** split R6 into app (API, UI, auth) and platform (Compose, CI, dashboards).

## Where we are (Sat 31 Oct)

| Done | Behind the plan |
|---|---|
| • Plan on `main` (24 Oct)<br/>• **Proof of concept v0 on `main`** (31 Oct): every box of the architecture at a basic level, 54 passing tests, the evaluation pipeline, simulated-student smoke test ([how to run it](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/poc/README.md))<br/>• **Live model ready:** each member puts their own course key in `.env` and runs `tutor check-llm` ([how](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/poc/README.md#using-a-real-model))<br/>• All tutor-visible data in `content/dataset-v0.10.0/`<br/>• Roles proposed (above)<br/>• NCERT files checked against our dataset ([findings](#what-we-found-on-31-oct)) | • Held-out freeze and hashes (R5)<br/>• Teaching policy (R1)<br/>• Spikes S1–S6<br/>• Compose skeleton (R6). CI exists but has not run on GitHub yet<br/>• The team build: due to start 26 Oct, it starts Mon 2 Nov |

**What this means:** the POC replaces Phase 1. Nobody rebuilds the skeleton. Each role **takes over its box in the POC and replaces the stand-in** with the real version (the "Planned" column of [What is real and what is still a stand-in](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/poc/README.md#what-is-real-and-what-is-still-a-stand-in)).

Building starts Mon 2 Nov, so **each milestone moves by about two days** (proposed as D-3; decided Sun 1 Nov). Submission and the viva don't move. To make room, four items from the [cut list](plan/09-delivery.md#risks-and-cut-lines) are **cut now**:
- the multi-query and rewrite ablation;
- Langfuse;
- the secondary quiz answered by the LLM;
- extra seeds for E2 and E4.

The per-layer E2 split stays, because it separates out the POC rule layer the Lead wrote ([D-1](DECISIONS.md)).

## What we found on 31 Oct

**1. The NCERT files someone shared are the official textbooks, not a second dataset.** They are the NCERT Class 10 Maths and Science textbooks, Reprint 2026-27: 33 PDFs, 508 pages.
- **They match our dataset.** Chapters 4, 5 and 8 (`jemh104`, `jemh105`, `jemh108`) have the same SHA-256 as the sources dataset v0.10.0 was built from. All 25 teaching cards' page anchors check out (hash, page, printed page, section). Our 25 concepts cover every teaching section: 4.2–4.4, 5.2–5.4 and 8.2–8.4.
- **What they add:** about 100 NCERT exercise questions in our three chapters, written independently of us.
- **What to watch:**
  - Plain text extraction breaks the maths: x² becomes "x2", "≠" disappears, and the n/2 in the AP sum is lost. Formulas come from our cards, not from the PDF text.
  - The answers appendix `jemh1an.pdf` answers every exercise in our chapters. Indexing it would let the tutor retrieve answers.
  - The Science half is outside our scope.
- **Recommended, decided Sun 1 Nov (D-4):**
  - Keep one copy in `data/ncert/`, which git ignores.
  - Index chapters 4, 5 and 8 only, and never the answers appendix.
  - Leave Science unused.
  - Type 20–30 NCERT exercises as a small external check set, kept out of git (R5b).

**2. The course API keys are personal OpenRouter keys,** valid until 16 Nov 2026. Each member has their own and must not share it. The 25 allowed models are in `course_models` in `config/app.toml`.
- **Two plan models are not on the list:** `openai/gpt-4.1`, the supervisor (**R3 picks a replacement**), and `meta-llama/llama-guard-4-12b`, the safety classifier (**R4 picks a replacement** in spike S4).
- The plan's other models are on the list: `gpt-4.1-mini`, `gemini-3.1-flash-lite` and `llama-3.3-70b-instruct`.
- [09 · Delivery](plan/09-delivery.md) stores one key as a GitHub secret. Keys are personal, so ask the faculty first, or run live evaluations locally.
- Both are open questions in [DECISIONS.md](DECISIONS.md#still-open).

## Timeline

Proposed on 31 Oct; the team confirms it on Sun 1 Nov (D-3).

| Date | Milestone | You check that… | Was |
|---|---|---|---|
| **Sat 31 Oct** | **R0 · Reset** | POC on `main`; a name on every role; everyone has run the POC | Fri 30 Oct |
| **Sun 1 Nov** | **Team meeting** | Roles, data rules and these dates agreed (D-2, D-3, D-4) | — |
| **Mon 2 Nov** | **M1 · Boxes owned** | Spikes S1–S6 answered; held-out frozen with hashes; teaching policy v1; CI green; every member has walked the team through their box | Sun 1 Nov |
| **Wed 4 Nov** | **M2 · All features basic** | `docker compose up` from a fresh clone; the x² = 5x question streams a cited hint from a real model; go/no-go on the cut list | Mon 2 Nov |
| **Fri 6 Nov** | **M3 · Behaviour frozen** | Every experiment configuration runs on 2 development cards; pre-registration hashed; CI green | Wed 4 Nov |
| **Sat 7 Nov** | **Human day** | Lesson review, judge labels, teacher approvals, all done by the named people. Runs start in the evening | Fri 6 Nov |
| **Mon 9 Nov** | **M4 · Results** | E1–E4 done, with three repeats where required; every number has a `run_id` | Sun 8 Nov |
| **Wed 11 Nov, 9 pm** | **Content freeze** | Report, slides, recording and README final. Only fixes after this | Same |
| **Thu 12 Nov, 6 pm** | **M5 · Submit** | Tag `v1.0`; submitted with six hours to spare, not at midnight | Same |
| **Sat 14 Nov** | **Mock viva** | Every member answers the [eight viva questions](plan/09-delivery.md#viva-preparation) | Same |
| **Sun 15 Nov** | **Review, demo and viva** | — | Same |

## Who owns which file

The POC keeps one file per component. **Each owner takes over their files as they are**, and moves code into folders (for example `guards.py` → `src/tutor/guardrails/`) in their own pull request when it grows. One person reorganising everything at once would conflict with everyone else's work.

| Path | Owner | Notes |
|---|---|---|
| `src/tutor/app.py` | R3 · Poonam | Session graph. The approval graph inside it is shared with R4 |
| `src/tutor/prompts.py`, `src/tutor/llm.py` | R3 · Poonam | R1 reviews prompts against the teaching policy |
| `src/tutor/learner.py` | R2 · Rizwan (mastery) · R3 · Poonam (planner) | Split into `memory/` and `graph/planner.py` when extended |
| `src/tutor/store.py`, `src/tutor/seed.py` | R2 · Rizwan | Moves to Postgres |
| `src/tutor/mcp_servers/` | R4 · Swati | `textbook_kb.py` with R2, who owns retrieval |
| `src/tutor/toolbus.py`, `approval_token.py`, `guards.py` | R4 · Swati | Hooks, approval tokens, guardrails |
| `src/tutor/mathcore.py` | R4 · Swati | Diagnosis rules in it: R3 + R2, rewritten from the catalogue |
| `src/socratic_data/` | Nobody edits | Vendored dataset kernel |
| `src/tutor/cli.py`, `config.py`, `config/` | R6 | Until the API and UI replace the CLI |
| `src/tutor_eval/`, `eval/` | R5 · Lakshya, with R5b | R5 and R5b never edit `mathcore.py`, `guards.py`, prompts or agents |
| `content/`, `Docs/policy/` | R1 · Lakshya | R2 ingests content |
| `tests/` | Each owner, for their part | — |

How to branch, review and log work: [CONTRIBUTING.md](../CONTRIBUTING.md).
