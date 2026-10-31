# Lead roadmap · 31 Oct → 15 Nov 2026

The team plan from Saturday 31 October to the viva: who owns what, what to ask each person for and when, and what counts as done. Written by the Lead; everyone works from it.

It re-dates [08 · Schedule](plan/08-schedule.md). **Where the two differ, this roadmap wins.** Everything else in the [plan](plan/README.md) still applies.

**Contents:**
- [Team](#team)
- [Where we are](#where-we-are-sat-31-oct)
- [What we found on 31 Oct](#what-we-found-on-31-oct)
- [Timeline](#timeline)
- [How to lead this project](#how-to-lead-this-project)
- [Your routine](#your-routine)
- [What to ask for, milestone by milestone](#what-to-ask-for-milestone-by-milestone)
- [Human-only tasks](#human-only-tasks-book-them-now)
- [When something slips](#when-something-slips)
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
| **R6** Deployment and operations | Shivam or Sharath (**to confirm which**) | Compose, API, UI, auth, Prometheus and Grafana, alerts, CI, README, demo recording | — |
| **R5b** Evaluation engineer (**proposed**) | The other of Shivam and Sharath | Judge runner, metrics, cost logging, report tables, the NCERT check set; second judge rater and held-out spot-checker. Builds on development data only; sees held-out cases only for the spot-check | **Edit prompts, agents, guards or diagnosis rules** |

**Why R5b:** six people and Lakshya holds two roles, so one person has no role yet. R5 carries the heaviest load in the last week, and R5b takes the parts that need no held-out access. **Fallback:** split R6 into app (API, UI, auth) and platform (Compose, CI, dashboards).

## Where we are (Sat 31 Oct)

| Done | Behind the plan |
|---|---|
| • Plan on `main` (24 Oct)<br/>• **Proof of concept v0 on `main`** (31 Oct): every box of the architecture at a basic level, 54 passing tests, the evaluation pipeline, simulated-student smoke test ([how to run it](poc/README.md))<br/>• **Live model ready:** each member puts their own course key in `.env` and runs `tutor check-llm` ([how](poc/README.md#using-a-real-model))<br/>• All tutor-visible data in `content/dataset-v0.10.0/`<br/>• Roles proposed (above)<br/>• NCERT files checked against our dataset ([findings](#what-we-found-on-31-oct)) | • Held-out freeze and hashes (R5)<br/>• Teaching policy (R1)<br/>• Spikes S1–S6<br/>• Compose skeleton (R6). CI exists but has not run on GitHub yet<br/>• The team build: due to start 26 Oct, it starts Mon 2 Nov |

**What this means:** the POC replaces Phase 1. Nobody rebuilds the skeleton. Each role **takes over its box in the POC and replaces the stand-in** with the real version (the "Planned" column of [What is real and what is still a stand-in](poc/README.md#what-is-real-and-what-is-still-a-stand-in)).

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

## How to lead this project

1. **Run on evidence, not status.** Every ask has a visible artefact: a merged pull request, a passing test, a trace, a `run_id` or a document. "Almost done" counts as not done. **Done means merged to `main` and shown in a demo.**
2. **Keep `main` working at all times.** Small pull requests every day. Nobody works more than a day without pushing their branch. Integration days are demos run from `main`, never from someone's laptop branch.
3. **Protect what carries the marks.** The [never-cut list](plan/09-delivery.md#risks-and-cut-lines): both signature challenges, held-out separation and pre-registration, the approval gate tied to the payload, counting failures, three repeats of E1 and E3, the one-command start, and honest limitations. Cut anything else early, in the cut-list order, rather than late.
4. **Enforce the separation rules from day one.** They cannot be added afterwards, and they decide whether E1–E4 count:
   - R3 (Poonam) never sees held-out cases.
   - R4 (Swati) never sees R5's new attacks before E2.
   - The diagnosis rules (R3 + R2) are written without reading R5's simulator.
5. **Book the human-only tasks now.** They are the ones that slip, and nothing can generate them ([list below](#human-only-tasks-book-them-now)).
6. **Record each decision on the day it is made,** in `Docs/DECISIONS.md`. The viva asks which experiment changed the design.
7. **Every member must defend their own box in the viva.** Ownership walkthroughs on Mon 2 Nov and pairing sessions after that are how they get there.

### Your own roles: Lead, R1 and R5

The day-by-day plan, with what Lakshya hands over and needs from each person, is in [roles/R1_R5_WORK_PLAN.md](roles/R1_R5_WORK_PLAN.md).

**R5 fits.** You generated the held-out cases and the attacks, and R5 is the role that holds them.

**But you also wrote the POC's diagnosis rules, guards and agents**, and the plan says R1 never writes attacks. So these hand-offs are needed to keep the separation rules intact:

| Rule at risk | What changes |
|---|---|
| The simulator and the diagnosis rules have different authors (rule 3) | **R3 (Poonam) + R2 (Rizwan) rewrite the POC's two diagnosis rules**, and write every new one, from the misconception catalogue, without reading `src/tutor_eval/`. You never edit `mathcore.py` again |
| The person building the defences does not write the attacks (rule 2) | **R4 (Swati) owns `guards.py`** and every guard layer; you never edit them. Your new attacks stay hidden from R4 until E2. E2 reports each defence layer separately, so the POC rule layer you wrote can be read on its own |
| R1 never writes attacks | **Your prompt reviews cover teaching only:** probes, hints, citations and the mode policy. **R4 alone decides refusal and safety wording** |
| The agent tuner never sees held-out cases (rule 1) | **You don't edit prompts or agents.** When you review them, cite only the teaching policy and development cases, never a held-out case |
| Nobody approves their own work | **R2 (Rizwan) approves your pre-registration wording.** **R5b, or R6, spot-checks 20 held-out cases** against your policy. **R5b, R4 or R6 is the second judge rater** |

**Two more rules for you:**
- **Keep held-out files out of git.** A private repository still lets R3 open them. Commit only the hashes and the manifest; keep the files on your machine and a private drive. Only the development split goes into `eval/dev/`.
- **State the arrangement in the report:** the POC's agents, guards, diagnosis rules and simulator, the 30 original attacks and the held-out cases share one author, and these are the hand-offs that followed.

**This is the heaviest load in the team.** Lead and R5 both peak in the same weeks. Hand off these drafts and keep only the review:

| Task | Draft by | You |
|---|---|---|
| Which models the course keys reach: `tutor check-llm --all`; a replacement for `gpt-4.1` | R3 (Poonam) | Measure the cost per session with the harness |
| Judge runner, metrics, cost logging, report tables | R5b | Review; you own the numbers |
| Demo script v1 | R6, who records the demo | Approve it |
| Slides | R2 (Rizwan), from your outline | Review them |

**You are the single point of failure.** You know the POC best. Walk each owner through their part on Mon 2 Nov, then stop being the person who fixes it.

#### Your calendar

| Date | As R5 | As R1 | As Lead |
|---|---|---|---|
| **Sat 31 Oct** | **Held-out freeze:** hashes and seed in `Docs/EXPERIMENT_LOG.md` | **Teaching policy v1** started. R3's prompts and R4's leak detector wait on it | POC on `main` ✓; roles posted ✓; meeting prepared |
| **Sun 1 Nov** | Development split into `eval/dev/`; development cost per 6-turn session (S6) | Teaching policy v1; book the teacher | **Team meeting**; record D-2, D-3, D-4 |
| **Mon 2 Nov** | Simulator rules started; harness skeleton | Held-out policy check, with the spot-checker | Ownership walkthroughs; **M1 check** |
| **Tue 3 Nov** | Simulator rules for every misconception seeded in the 40 cards; harness runs C1 against C2; section-query labels with R2 | Teacher reviews the catalogue and rubric | — |
| **Wed 4 Nov** | At least 10 new attacks with controls (kept from R4); leak and diagnosis metrics with R5b | Run the demo script on `main`; file gaps | **M2 go/no-go** |
| **Thu 5 Nov** | Simulator validation; pre-registration to R2 for approval | Lesson-review rubric | — |
| **Fri 6 Nov** | Pre-registration frozen and hashed; development golden run; Reflexion iteration 2 with R3 | — | **M3 check** |
| **Sat 7 Nov** | Freeze the playbook; compute kappa; evening: E1 seed 1, E2, E3 seed 1 | Lesson review; judge labels with R5b, R4 or R6; approve question sets as teacher (disclosed) | Human day |
| **Sun 8 Nov** | E4a, E4b, deployment configuration; E1 and E3 seed 2 | — | — |
| **Mon 9 Nov** | E1 and E3 seed 3; results tables (R5b drafts) | Slide outline to R2 | **M4 check** |
| **Tue 10 Nov** | Report draft: data, method, results. Others write their own sections | Review the draft | — |
| **Wed 11 Nov** | Final report | Demo recording with R6 | **Content freeze, 9 pm** |
| **Thu 12 Nov** | Final checks | — | **Submit by 6 pm** |

**If Sat 31 Oct – Wed 4 Nov overruns, keep this order:**
1. The held-out freeze and the development split. They block R2, R3 and the experiments.
2. The teaching policy. It blocks R3 and R4.
3. The simulator and the harness.
4. The new attacks and the judge. E2 is not until Sat 7, so these can slip a day.

## Your routine

| When | Time | What you do |
|---|---|---|
| **Daily stand-up**, at a fixed time | 15 min | Each person: what they merged yesterday, what they will merge today, and blockers. You write the blockers down; you don't solve them in the call |
| After stand-up | 10 min | Tick the milestone checklist. Message anyone with no pull request in 24 hours |
| Evening | 15 min | Check open pull requests have a reviewer and `main` is green. Merge what is approved |
| **Integration days:** Mon 2, Wed 4, Fri 6, Mon 9 Nov | 60–90 min | Everyone demos from `main`. You run the exit check and record go/no-go in `Docs/DECISIONS.md` |
| Each week | 30 min per member | One pairing session in which a member explains their box to someone in another role. This is viva practice |

**Tracking:** create one GitHub issue per milestone, paste that milestone's checklist from below, and assign each line to its owner. Checkboxes in issues can be ticked; checkboxes in this file cannot. **Day-to-day messages go in the team WhatsApp group;** decisions made there are copied into `Docs/DECISIONS.md` the same day.

## What to ask for, milestone by milestone

Each line is a deliverable, followed (after →) by **the evidence to ask for**.

### Sat 31 Oct – Sun 1 Nov · R0 Reset

**You:**
- [x] Merge the POC, this roadmap and the live-model setup into `main` → done 31 Oct, before branch protection
- [x] Post the roles in the group and fill in the tables → D-2; confirm R6's name and the sixth member's role on Sunday
- [ ] Turn on branch protection for `main` (pull request + 1 review + CI must pass) and add everyone as a collaborator → GitHub Settings → Branches
- [ ] Keep the full dataset build with you (you are R5). Share nothing held-out, in git or in chat → only the development split goes into `eval/dev/`
- [ ] Fix the stand-up time, and book Sat 7 Nov as the human day → calendar invite sent
- [ ] Create the milestone issues → issues exist

**Everyone:**
- [ ] Install and run the POC with the [setup guide](SETUP.md) → screenshot of `pytest -q` showing every test passed, and of `tutor check-llm` passing with their own key
- [ ] Read the POC code for their box ([who owns which file](#who-owns-which-file)) and its row in [10 · Proof of concept](plan/10-proof-of-concept.md#what-each-box-looks-like-in-the-poc) → can explain it at Monday's walkthrough
- [ ] First entry in [Docs/CONTRIBUTIONS.md](CONTRIBUTIONS.md) → entry merged

### Sun 1 – Mon 2 Nov · M1 Boxes owned

| Role | Ask for | Evidence |
|---|---|---|
| **R1** · Lakshya | Teaching and mode policy, leak definition and the after-the-last-hint policy, in `Docs/policy/TEACHING_POLICY.md`. Book the teacher, or record that R1 acts as teacher. Approve demo script v1 (R6 drafts it) | PR merged; teacher date fixed |
| **R2** · Rizwan | Spike S3: Docling or PyMuPDF on three Chapter 4 pages. Chapter 4 ingested into hybrid retrieval in `textbook-kb` (bm25s, fastembed, RRF): **chapters 4, 5 and 8 only, never the answers appendix** (D-4). Baseline Recall@5 on the 15 development card queries | `Docs/spikes/S3.md`; PR; the number in `Docs/EXPERIMENT_LOG.md` |
| **R3** · Poonam | Spike S2: interrupt and resume across a restart with the Postgres checkpointer. `tutor check-llm --all` with your own key, and a replacement for the `gpt-4.1` supervisor. Specialists move from templates to `create_agent` on the course key. Planner with structured output. **With R2: rewrite the POC's two diagnosis rules from the misconception catalogue, without reading `src/tutor_eval/`** | Spike note; a trace of the x² = 5x question answered by a real model; diagnosis tests green |
| **R4** · Swati | Spike S1: the LangChain MCP adapter or the hand-written one. The four servers run over stdio or HTTP, not only in memory. Spike S4: **Llama Guard 4 is not on the course key list**, so choose and test a replacement safety classifier; Prompt Guard 2 latency on CPU | Two spike notes; tool tests green |
| **R5** · Lakshya | **Held-out freeze:** seed and hashes in `Docs/EXPERIMENT_LOG.md`; held-out files stay out of git. Development split shared in `eval/dev/`. Spike S6: the cost of a 6-turn session | Hashes committed; `Docs/spikes/S6.md` |
| **R6** · to confirm | Spike S5: compose with postgres, chroma, prometheus and grafana, with health checks. First green CI run on a pull request. `CODEOWNERS` from the [ownership table](#who-owns-which-file), with GitHub usernames. Draft demo script v1 for R1 | A green CI run; `docker compose up --wait` output |
| **R5b** · proposed | Judge runner skeleton on POC transcripts. Spot-check 20 held-out cases against the teaching policy (shown by R5, not copied). Type 20–30 NCERT exercises as typed problems with kernel keys, kept out of git | Runner PR; spot-check notes; the check set's hash |

**Exit, Monday evening:** all six spike notes in `Docs/spikes/`; CI green; held-out hashes logged; a 10-minute walkthrough of each box.

### Tue 3 – Wed 4 Nov · M2 All features basic

| Role | Ask for |
|---|---|
| **R1** | Run the demo script on `main`; file each gap as an issue |
| **R2** | Mastery, misconceptions and styles in the Postgres store; a memory on/off switch; all 25 cards indexed |
| **R3** | Outer-fringe planner over all 25 concepts; replan triggers; the stuck rule; more diagnosis rules (with R2); fixtures for the two demo learners |
| **R4** | Input guards (Prompt Guard 2 and the chosen safety classifier) and output guards (leak detector, citation validator); mode rules; the HMAC approval gate behind the API |
| **R5** | Simulator rules for every misconception seeded in the 40 cards; the harness runs C1 against C2; a security runner that writes dataset observations; **at least 10 new attacks with controls, kept from R4** |
| **R5b** | Judge prompt and runner; leak and diagnosis metrics; cost logging per session |
| **R6** | API: `/chat` with SSE, `/chat/resume`, `/teacher/approvals`. Streamlit chat and teacher pages. One Grafana panel row; the leak-alert script |

**Exit, Wednesday:**
- From a fresh clone, `docker compose up` starts everything.
- The x² = 5x question streams a cited Socratic hint from a real model, and the trace shows every box.
- Two learners get different teaching, and a quiz triggers a replan (signature A).
- An edit invalidates an approval, from the teacher page.
- The harness runs C1 against C2 on 2 development cards with R5's simulator.

**Then decide go/no-go on the [cut list](plan/09-delivery.md#risks-and-cut-lines)** and record it.

### Thu 5 – Fri 6 Nov · M3 Behaviour frozen

| Role | Ask for |
|---|---|
| **R1** | Prepare the lesson-review rubric |
| **R2** | Memory policy v1; reranker before and after on both query sets; final retrieval numbers. **Approve the pre-registration wording** (R1 and R5 are one person, so R2 approves) |
| **R3** | C0 and C1 baselines; the Reflexion loop; iteration 1 on Thu 5 and iteration 2 with R5 on Fri 6, giving candidate lessons |
| **R4** | Threat model v1; guard tests; an on/off switch for each defence layer |
| **R5** | Simulator validation; development run of the golden set; pre-registration frozen on Fri 6, with its hash logged; refreshed cost estimate |
| **R5b** | Results-table scripts on development runs; kappa code ready for Saturday |
| **R6** | `eval-gate` CI job; compose smoke test; README v1; first clean install on a second machine |

**Exit, Friday:** agent behaviour frozen (except the playbook); every experiment configuration runs on 2 development cards without errors; pre-registration hashed; CI green.

### Sat 7 – Mon 9 Nov · M4 Results

| Day | Who | Work |
|---|---|---|
| **Sat 7 · human day** | R1 (+ teacher) | Lesson review, with at least one rejection and its reason |
| | R5 | Freeze the playbook (tag `playbook-v1`, record its hash) |
| | R1 + R5b, R4 or R6 | Judge labels on 30 turns; R5 computes kappa |
| | Teacher or R1 | Approve question sets (recorded) |
| | R5 (evening) | E1 seed 1, E2, E3 seed 1 |
| **Sun 8** | R5 + R5b | E4a, E4b and the deployment configuration; E1 and E3 seed 2 |
| | R6 | Watch the dashboards; fire the leak alert |
| **Mon 9** | R5 + R5b | E1 and E3 seed 3; results tables with spread |
| | R6 | The deliberate failed CI run and `Docs/ci_failure.md`; a clean-machine install by someone who has never run the stack |

**Your exit check:**
- Every number traces back to a `run_id`.
- Failed runs are counted.
- No POC number is quoted as a result.

### Tue 10 – Thu 12 Nov · M5 Submission

| Day | Ask for |
|---|---|
| **Tue 10** | Evaluation report draft (R5 leads; each role writes its own section). R3 + R6: our redrawn architecture diagram and the numbered walkthrough from a real trace. R4: final threat model. R2: final memory policy. Slides draft: R2 from R1's outline |
| **Wed 11** | R6 + R1: backup demo recording. Final README, final clean install, final report. **Content freeze at 9 pm** |
| **Thu 12** | Final checks: no keys, PDFs, page images or private data in the repository, and `pip-audit` passes. Tag `v1.0`. **Submit by 6 pm** |

### Fri 13 – Sun 15 Nov · Viva

- **Fri 13:** every member redraws the full architecture from memory and explains every box.
- **Sat 14:** mock viva. You play the examiner and ask each person the eight questions, with their traces.
- **Sun 15:** review, demo and viva.

## Human-only tasks: book them now

These count as done only when the named person has done them. Nothing generated or inferred replaces them.

| Task | Who | New date | Was |
|---|---|---|---|
| A name on every role; start the contribution log | All | Sun 1 Nov | Fri 30 Oct |
| Freeze the held-out golden subset, held-out students and attack list; record hashes | R5 | Sun 1 Nov, before the meeting | Sat 31 Oct |
| Check the held-out cases against the written policy | R1, plus a spot-check of 20 cases by R5b (or R6) | Mon 2 Nov | Sun 1 Nov |
| Confirm the 42 card labels; write and label 45 section queries | R2 + R5 | Mon 2 – Tue 3 Nov | Sun 1 – Mon 2 Nov |
| Teacher reviews the misconception catalogue and rubric | R1 + teacher | By Tue 3 Nov | Same |
| At least 10 new attacks, each with a control | R5 | Wed 4 Nov | Tue 3 Nov |
| Lesson review, with at least one rejection | R1 (+ teacher) | Sat 7 Nov | Fri 6 Nov |
| Judge labels: 30 turns, two raters | R1 + R5b, R4 or R6 | Sat 7 Nov | Fri 6 Nov |
| Teacher approves the first question sets, live | Teacher, or R1 acting as teacher (disclosed) | Sat 7 Nov and the demo | Fri 6 Nov |
| Interpret results; individual viva | All | 10–15 Nov | 9–15 Nov |

## When something slips

| Signal | What you do |
|---|---|
| A member has no pull request for 24 hours | Message them the same day and pair them with someone |
| A milestone item is one day late | Shrink it to a smaller version that still demos, or reassign it |
| M2 is missed | Apply the [cut list](plan/09-delivery.md#risks-and-cut-lines) in order, and record each cut in `Docs/DECISIONS.md` |
| A member drops out | Use the [reduced-team plan](plan/07-team-and-roles.md#if-fewer-than-six-people-are-active): R1+R6, R2, R3, R4+R5. The held-out freeze and new attacks must still come from someone who is neither the R3 nor the R4 person. R5b's work goes back to R5 |
| Usage limits on a course key | Ask the faculty early; cut the extra E2 and E4 seeds first. Keys expire on 16 Nov, the day after the viva |
| Docker is too heavy on laptops | One shared machine runs the full stack for demos; others run the POC way (no Docker) |

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
