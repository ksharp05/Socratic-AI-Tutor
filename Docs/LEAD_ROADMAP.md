# Lead roadmap · 30 Oct → 15 Nov 2026

How the lead runs the project from Friday 30 October to the viva: what to ask each person for, when, and what counts as done.

It re-dates [08 · Schedule](plan/08-schedule.md) from today. **Where the two differ, this roadmap wins.** Everything else in the [plan](plan/README.md) still applies.

**Contents:**
- [Where we are](#where-we-are-fri-30-oct)
- [Timeline](#timeline)
- [How to lead this project](#how-to-lead-this-project)
- [Your routine](#your-routine)
- [What to ask for, milestone by milestone](#what-to-ask-for-milestone-by-milestone)
- [Human-only tasks](#human-only-tasks-book-them-now)
- [When something slips](#when-something-slips)
- [Who owns which file](#who-owns-which-file)

## Where we are (Fri 30 Oct)

| Done | Overdue against the plan |
|---|---|
| • Plan proposed on `main` (24 Oct)<br/>• **Proof of concept v0** on branch `poc/walking-skeleton`: every box of the architecture at a basic level, 25 passing tests, simulated-student smoke test ([how to run it](poc/README.md))<br/>• All tutor-visible data in `content/dataset-v0.10.0/` | • Role names (M0, 25 Oct)<br/>• Held-out freeze and hashes (R5, 25 Oct)<br/>• Teaching policy (R1, 26 Oct)<br/>• Spikes S1–S6 (26 Oct)<br/>• Compose skeleton and CI (R6, 26 Oct)<br/>• M1 walking skeleton (today) |

**What this means:** the POC replaces Phase 1. Nobody rebuilds the skeleton. Each role **takes over its box in the POC and replaces the stand-in** with the real version (the "Planned" column of [What is real and what is still a stand-in](poc/README.md#what-is-real-and-what-is-still-a-stand-in)).

That buys back the lost week. **Every date from M2 (Mon 2 Nov) onward stays as planned.**

## Timeline

| Date | Milestone | You check that… |
|---|---|---|
| **Fri 30 Oct** | **R0 · Reset** | POC merged to `main`; six names against R1–R6; everyone has run the POC |
| **Sun 1 Nov** | **M1 · Boxes owned** (moved from 30 Oct) | Spikes S1–S6 answered; held-out frozen with hashes; teaching policy v1; CI green; every member has walked the team through their box |
| **Mon 2 Nov** | **M2 · All features basic** | `docker compose up` from a fresh clone; the x² = 5x question streams a cited hint from a real model; go/no-go on the cut list |
| **Wed 4 Nov** | **M3 · Behaviour frozen** | Every experiment configuration runs on 2 development cards; pre-registration hashed; CI green |
| **Fri 6 Nov** | **Human day** | Lesson review, judge labels, teacher approvals, all done by the named people |
| **Sun 8 Nov** | **M4 · Results** | E1–E4 done, with three repeats where required; every number has a `run_id` |
| **Wed 11 Nov, 9 pm** | **Content freeze** | Report, slides, recording and README final. Only fixes after this |
| **Thu 12 Nov, 6 pm** | **M5 · Submit** | Tag `v1.0`; submitted with six hours to spare, not at midnight |
| **Sat 14 Nov** | **Mock viva** | Every member answers the [eight viva questions](plan/09-delivery.md#viva-preparation) |
| **Sun 15 Nov** | **Review, demo and viva** | — |

## How to lead this project

1. **Run on evidence, not status.** Every ask has a visible artefact: a merged pull request, a passing test, a trace, a `run_id` or a document. "Almost done" counts as not done. **Done means merged to `main` and shown in a demo.**
2. **Keep `main` working at all times.** Small pull requests every day. Nobody works more than a day without pushing their branch. Integration days are demos run from `main`, never from someone's laptop branch.
3. **Protect what carries the marks.** The [never-cut list](plan/09-delivery.md#risks-and-cut-lines): both signature challenges, held-out separation and pre-registration, the approval gate tied to the payload, counting failures, three repeats of E1 and E3, the one-command start, and honest limitations. Cut anything else early, in the cut-list order, rather than late.
4. **Enforce the separation rules from day one.** They cannot be added afterwards, and they decide whether E1–E4 count:
   - R3 never sees held-out cases.
   - R4 never sees R5's new attacks before E2.
   - The diagnosis rules (R3 + R2) are written without reading R5's simulator.
5. **Book the human-only tasks now.** They are the ones that slip, and nothing can generate them ([list below](#human-only-tasks-book-them-now)).
6. **Record each decision on the day it is made,** in `Docs/DECISIONS.md`. The viva asks which experiment changed the design.
7. **Every member must defend their own box in the viva.** Ownership walkthroughs this weekend and pairing sessions next week are how they get there.

### Your own roles: Lead, R1 and R5

**R5 fits.** You generated the held-out cases and the attacks, and R5 is the role that holds them.

**But you also wrote the POC's diagnosis rules, guards and agents**, and the plan says R1 never writes attacks. So these hand-offs are needed to keep the separation rules intact:

| Rule at risk | What changes |
|---|---|
| The simulator and the diagnosis rules have different authors (rule 3) | **R3 + R2 rewrite the POC's two diagnosis rules**, and write every new one, from the misconception catalogue, without reading `src/tutor_eval/`. You never edit `mathcore.py` again |
| The person building the defences does not write the attacks (rule 2) | **R4 owns `guards.py`** and every guard layer; you never edit them. Your new attacks stay hidden from R4 until E2. E2 reports each defence layer separately, so the POC rule layer you wrote can be read on its own |
| R1 never writes attacks | **Your prompt reviews cover teaching only:** probes, hints, citations and the mode policy. **R4 alone decides refusal and safety wording** |
| The agent tuner never sees held-out cases (rule 1) | **You don't edit prompts or agents.** When you review them, cite only the teaching policy and development cases, never a held-out case |
| Nobody approves their own work | **R2 approves your pre-registration wording.** **R6 spot-checks 20 held-out cases** against your policy. **R4 or R6 is the second judge rater** |

**Two more rules for you:**
- **Keep held-out files out of git.** A private repository still lets R3 open them. Commit only the hashes and the manifest; keep the files on your machine and a private drive. Only the development split goes into `eval/dev/`.
- **State the arrangement in the report:** the POC's agents, guards, diagnosis rules and simulator, the 30 original attacks and the held-out cases share one author, and these are the hand-offs that followed.

**This is the heaviest load in the team.** Lead and R5 both peak in the same weeks. Hand off these drafts and keep only the review:

| Task | Draft by | You |
|---|---|---|
| Which models the faculty keys reach (part of spike S6) | R3, who needs the key first anyway | Measure the cost per session with the harness |
| Demo script v1 | R6, who records the demo | Approve it |
| Slides | R2, from your outline | Review them |

**You are the single point of failure.** You know the POC best. Walk each owner through their part on Saturday, then stop being the person who fixes it.

#### Your calendar

| Date | As R5 | As R1 | As Lead |
|---|---|---|---|
| **Fri 30 Oct** | — | — | Merge the POC; names; branch protection; milestone issues; book Fri 6 |
| **Sat 31 Oct** | **Held-out freeze:** hashes and seed in `Docs/EXPERIMENT_LOG.md`. Development split into `eval/dev/` | **Teaching policy v1.** R3's prompts and R4's leak detector wait on it | Ownership walkthroughs |
| **Sun 1 Nov** | Development cost per 6-turn session (S6) | Held-out policy check, with R6's spot-check; book the teacher | **M1 check** |
| **Mon 2 Nov** | Simulator rules for every misconception seeded in the 40 cards; harness runs C1 against C2 | Run the demo script on `main`; file gaps | **M2 go/no-go** |
| **Tue 3 Nov** | At least 10 new attacks with controls (kept from R4); judge runner; leak and diagnosis metrics; section-query labels with R2 | Teacher reviews the catalogue and rubric | — |
| **Wed 4 Nov** | Simulator validation; pre-registration frozen and hashed, after R2 approves it | Lesson-review rubric | **M3 check** |
| **Thu 5 Nov** | Development golden run; Reflexion iteration 2 with R3 | — | — |
| **Fri 6 Nov** | Freeze the playbook; compute kappa | Lesson review; judge labels with R4 or R6; approve question sets as teacher (disclosed) | Human day |
| **Sat 7 Nov** | E1 seed 1, E2, E3 seed 1, E4a, E4b, deployment configuration | — | — |
| **Sun 8 Nov** | E1 and E3 seeds 2 and 3; results tables | — | **M4 check** |
| **Mon 9 – Tue 10 Nov** | Report draft: data, method, results. Others write their own sections | Slide outline to R2; review the draft | — |
| **Wed 11 Nov** | Final report | Demo recording with R6 | **Content freeze, 9 pm** |
| **Thu 12 Nov** | Final checks | — | **Submit by 6 pm** |

**If Sat 31 Oct – Tue 3 Nov overruns, keep this order:**
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
| **Integration days:** Sun 1, Mon 2, Wed 4, Sun 8 Nov | 60–90 min | Everyone demos from `main`. You run the exit check and record go/no-go in `Docs/DECISIONS.md` |
| Each week | 30 min per member | One pairing session in which a member explains their box to someone in another role. This is viva practice |

**Tracking:** create one GitHub issue per milestone, paste that milestone's checklist from below, and assign each line to its owner. Checkboxes in issues can be ticked; checkboxes in this file cannot.

## What to ask for, milestone by milestone

Each line is a deliverable, followed (after →) by **the evidence to ask for**.

### Today, Fri 30 Oct · R0 Reset

**You:**
- [ ] Open the pull request from `poc/walking-skeleton` to `main`, ask one member to review it, and merge → PR merged
- [ ] Post the team message; confirm six names; fill in the table in [07 · Team and roles](plan/07-team-and-roles.md) → names in `main`
- [ ] Turn on branch protection for `main` (pull request + 1 review + CI must pass) and add everyone as a collaborator → GitHub Settings → Branches
- [ ] Keep the full dataset build with you (you are R5). Share nothing held-out, in git or in chat → only the development split goes into `eval/dev/`
- [ ] Fix the stand-up time, and book Fri 6 Nov as the human day → calendar invite sent
- [ ] Create the milestone issues → issues exist

**Everyone:**
- [ ] Install and run the POC ([Docs/poc/README.md](poc/README.md)) → screenshot of `pytest -q` showing 30 passed, and of `tutor check-llm` passing with their own key
- [ ] Read the POC code for their box ([who owns which file](#who-owns-which-file)) and its row in [10 · Proof of concept](plan/10-proof-of-concept.md#what-each-box-looks-like-in-the-poc) → can explain it at Sunday's walkthrough
- [ ] First entry in [Docs/CONTRIBUTIONS.md](CONTRIBUTIONS.md) → entry merged

### Sat 31 Oct – Sun 1 Nov · M1 Boxes owned

| Role | Ask for | Evidence |
|---|---|---|
| **R1** | Teaching and mode policy, leak definition and the after-the-last-hint policy, in `Docs/policy/TEACHING_POLICY.md`. Book the teacher, or record that R1 acts as teacher. Approve demo script v1 (R6 drafts it) | PR merged; teacher date fixed |
| **R2** | Spike S3: Docling or PyMuPDF on three Chapter 4 pages. Chapter 4 ingested into hybrid retrieval in `textbook-kb` (bm25s, fastembed, RRF). Baseline Recall@5 on the 15 development card queries | `Docs/spikes/S3.md`; PR; the number in `Docs/EXPERIMENT_LOG.md` |
| **R3** | Spike S2: interrupt and resume across a restart with the Postgres checkpointer. Which models the faculty keys reach (part of S6). Specialists move from templates to `create_agent` on the faculty key. Planner with structured output. **With R2: rewrite the POC's two diagnosis rules from the misconception catalogue, without reading `src/tutor_eval/`** | Spike note; a trace of the x² = 5x question answered by a real model; diagnosis tests green |
| **R4** | Spike S1: the LangChain MCP adapter or the hand-written one. The four servers run over stdio or HTTP, not only in memory. Spike S4: Llama Guard 4 output parsing and Prompt Guard 2 latency on CPU | Two spike notes; tool tests green |
| **R5** | **Held-out freeze:** seed and hashes in `Docs/EXPERIMENT_LOG.md`; held-out files stay out of git. Development split shared in `eval/dev/`. Spike S6: the cost of a 6-turn session | Hashes committed; `Docs/spikes/S6.md` |
| **R6** | Spike S5: compose with postgres, chroma, prometheus and grafana, with health checks. CI runs `pytest` on every pull request. `CODEOWNERS` from the [ownership table](#who-owns-which-file). Draft demo script v1 for R1. Spot-check 20 held-out cases against the teaching policy | A green CI run; `docker compose up --wait` output |

**Exit, Sunday evening:** all six spike notes in `Docs/spikes/`; CI green; held-out hashes logged; a 10-minute walkthrough of each box.

### Mon 2 Nov · M2 All features basic (integration day)

| Role | Ask for |
|---|---|
| **R1** | Run the demo script on `main`; file each gap as an issue |
| **R2** | Mastery, misconceptions and styles in the Postgres store; a memory on/off switch; all 25 cards indexed |
| **R3** | Outer-fringe planner over all 25 concepts; replan triggers; the stuck rule; more diagnosis rules (with R2); fixtures for the two demo learners |
| **R4** | Input guards (Prompt Guard 2, Llama Guard 4) and output guards (leak detector, citation validator); mode rules; the HMAC approval gate behind the API |
| **R5** | Simulator rules for every misconception seeded in the 40 cards; the harness runs C1 against C2; a security runner that writes dataset observations. **By Tue 3:** judge prompt and runner, leak and diagnosis metrics, and **at least 10 new attacks with controls, kept from R4** |
| **R6** | API: `/chat` with SSE, `/chat/resume`, `/teacher/approvals`. Streamlit chat and teacher pages. One Grafana panel row; the leak-alert script |

**Exit:**
- From a fresh clone, `docker compose up` starts everything.
- The x² = 5x question streams a cited Socratic hint from a real model, and the trace shows every box.
- Two learners get different teaching, and a quiz triggers a replan (signature A).
- An edit invalidates an approval, from the teacher page.
- The harness runs C1 against C2 on 2 development cards with R5's simulator.

**Then decide go/no-go on the [cut list](plan/09-delivery.md#risks-and-cut-lines)** and record it.

### Tue 3 – Wed 4 Nov · M3 Behaviour frozen

| Role | Ask for |
|---|---|
| **R1** | Prepare the lesson-review rubric |
| **R2** | Memory policy v1; reranker before and after on both query sets. **Approve the pre-registration wording** (R1 and R5 are one person, so R2 approves) |
| **R3** | C0 and C1 baselines; the Reflexion loop; first development iteration on Wed 4 |
| **R4** | Threat model v1; guard tests; an on/off switch for each defence layer |
| **R5** | Simulator validation; pre-registration frozen on Wed 4, with its hash logged; refreshed cost estimate |
| **R6** | `eval-gate` CI job; compose smoke test; README v1; first clean install on a second machine |

**Exit:** agent behaviour frozen (except the playbook); every experiment configuration runs on 2 development cards without errors; pre-registration hashed; CI green.

### Thu 5 – Sun 8 Nov · M4 Results

| Day | Who | Work |
|---|---|---|
| **Thu 5** | R3 + R5 | Second Reflexion iteration, giving candidate lessons |
| | R2 | Final retrieval numbers, before and after |
| | R5 | Development run of the golden set |
| **Fri 6 · human day** | R1 (+ teacher) | Lesson review, with at least one rejection and its reason |
| | R5 | Freeze the playbook (tag `playbook-v1`, record its hash) |
| | R1 + R4 or R6 | Judge labels on 30 turns; R5 computes kappa |
| | Teacher or R1 | Approve question sets (recorded) |
| **Sat 7** | R5 | E1 seed 1, E2, E3 seed 1, E4a, E4b and the deployment configuration |
| | R6 | Watch the dashboards; fire the leak alert |
| **Sun 8** | R5 | E1 and E3 seeds 2 and 3; results tables with spread |
| | R6 | The deliberate failed CI run and `Docs/ci_failure.md`; a clean-machine install by someone who has never run the stack |

**Your exit check:**
- Every number traces back to a `run_id`.
- Failed runs are counted.
- No POC number is quoted as a result.

### Mon 9 – Thu 12 Nov · M5 Submission

| Day | Ask for |
|---|---|
| **Mon 9** | R3 + R6: our redrawn architecture diagram and the numbered walkthrough from a real trace. R4: final threat model. R2: final memory policy |
| **Tue 10** | Evaluation report draft (R5 leads; each role writes its own section). Slides draft: R2 from R1's outline |
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
| Six names; start the contribution log | All | Fri 30 Oct | 25 Oct |
| Freeze the held-out golden subset, held-out students and attack list; record hashes | R5 | Sat 31 Oct | 25 Oct |
| Check the held-out cases against the written policy | R1, plus R6's spot-check of 20 cases | Sun 1 Nov | 26 Oct |
| Confirm the 42 card labels; write and label 45 section queries | R2 + R5 | Sun 1 – Mon 2 Nov | 27–28 Oct |
| Teacher reviews the misconception catalogue and rubric | R1 + teacher | By Tue 3 Nov | 29 Oct |
| At least 10 new attacks, each with a control | R5 | Tue 3 Nov | 2 Nov |
| Lesson review, with at least one rejection | R1 (+ teacher) | Fri 6 Nov | Same |
| Judge labels: 30 turns, two raters | R1 + R4 or R6 | Fri 6 Nov | Same |
| Teacher approves the first question sets, live | Teacher, or R1 acting as teacher (disclosed) | Fri 6 Nov and the demo | Same |
| Interpret results; individual viva | All | 9–15 Nov | Same |

## When something slips

| Signal | What you do |
|---|---|
| A member has no pull request for 24 hours | Message them the same day and pair them with someone |
| A milestone item is one day late | Shrink it to a smaller version that still demos, or reassign it |
| M2 is missed | Apply the [cut list](plan/09-delivery.md#risks-and-cut-lines) in order, and record each cut in `Docs/DECISIONS.md` |
| A member drops out | Use the [reduced-team plan](plan/07-team-and-roles.md#if-fewer-than-six-people-are-active): R1+R6, R2, R3, R4+R5. The held-out freeze and new attacks must still come from someone who is neither the R3 nor the R4 person |
| Usage limits on the faculty keys | Ask the faculty early; cut the extra E2 and E4 seeds first |
| Docker is too heavy on laptops | One shared machine runs the full stack for demos; others run the POC way (no Docker) |

## Who owns which file

The POC keeps one file per component. **Each owner takes over their files as they are**, and moves code into folders (for example `guards.py` → `src/tutor/guardrails/`) in their own pull request when it grows. One person reorganising everything at once would conflict with everyone else's work.

| Path | Owner | Notes |
|---|---|---|
| `src/tutor/app.py` | R3 | Session graph. The approval graph inside it is shared with R4 |
| `src/tutor/prompts.py`, `src/tutor/llm.py` | R3 | R1 reviews prompts against the teaching policy |
| `src/tutor/learner.py` | R2 (mastery) · R3 (planner) | Split into `memory/` and `graph/planner.py` when extended |
| `src/tutor/store.py`, `src/tutor/seed.py` | R2 | Moves to Postgres |
| `src/tutor/mcp_servers/` | R4 | `textbook_kb.py` with R2, who owns retrieval |
| `src/tutor/toolbus.py`, `approval_token.py`, `guards.py` | R4 | Hooks, approval tokens, guardrails |
| `src/tutor/mathcore.py` | R4 | Diagnosis rules in it: R3 + R2, rewritten from the catalogue |
| `src/socratic_data/` | Nobody edits | Vendored dataset kernel |
| `src/tutor/cli.py`, `config.py`, `config/` | R6 | Until the API and UI replace the CLI |
| `src/tutor_eval/`, `eval/` | R5 | R5 never edits `mathcore.py`, `guards.py`, prompts or agents |
| `content/`, `Docs/policy/` | R1 | R2 ingests content |
| `tests/` | Each owner, for their part | — |

How to branch, review and log work: [CONTRIBUTING.md](../CONTRIBUTING.md).
