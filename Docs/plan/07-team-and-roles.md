# 07 · Team and roles

[← Security and privacy](06-security-and-privacy.md) · [Plan overview](README.md) · [Next: Schedule →](08-schedule.md)

## Roles

Names proposed in the team group on 31 Oct ([D-2](../DECISIONS.md)); confirmed at the meeting on Sun 1 Nov. The [lead roadmap](../LEAD_ROADMAP.md#team) has the current table, including the proposed sixth role, R5b.

| Role | Name | Owns (code and documents) | Never does |
|---|---|---|---|
| **R1** Domain and product lead | Lakshya Yadav (ksharp05; also Lead and R5), with everyone contributing | Teaching and mode policy; definition of an answer leak; policy for what happens after the last hint; review of the misconception catalogue (with the teacher); demo script; held-out policy check; lesson review; judge labels; slides | Write attacks |
| **R2** Knowledge and memory engineer | Rizwan Farooq | `tutor/retrieval/`, the ingest job, section labels (with R5), `tutor/memory/` (mastery model, store, summarisation, forget-me), memory policy | — |
| **R3** Agents and orchestration engineer | Poonam Ramnaresh Prajapati | `tutor/graph/`, agents and prompts, planner, self-correction loop, C0 and C1 baselines, Reflexion code, diagnosis rules (with R2) | **Read `eval/private/`, or look at held-out results before the freeze** |
| **R4** Tools, control and security engineer | Swati Smita Biswal | `tutor/mcp_servers/`, hooks, guardrails, approval gate, answer adapter, threat model | **See R5's new attacks before E2** |
| **R5** Evaluation and red-team engineer | Lakshya Yadav (ksharp05; also Lead and R1) | `eval/` (harness, simulator engine and rules, judge, scorers, configurations, pre-registration), the held-out freeze, new attacks, results tables | **Edit prompts, agents or guards** |
| **R6** Deployment and operations engineer | Sharath S Nadig (confirmed 13 Nov) | Compose, Dockerfiles, API, UI, authentication, Prometheus and Grafana, alerting, CI, README, clean-machine test, demo recording | — |

## Separation rules

The guide requires two separations, and we add a third:

1. **The person tuning the agents does not write or see the held-out cases.** R5 owns the held-out sets, and R3 never reads them.
2. **The person building the defences does not write the attacks.** R5 writes them, and R4 sees the new ones only after E2.
3. **The simulator and the diagnostician are written by different people.** R5 writes the simulator's buggy rules; R2 and R3 write the diagnostician's rules. Both work from the shared misconception catalogue, so the evaluation never grades its own answer key.

`CODEOWNERS` enforces review by R5 on `eval/` and by R4 on `tutor/guardrails/`.

## Working agreements

- **Daily stand-up:** 15 minutes, at a time we fix at kickoff.
- **Contribution log:** every member appends to `Docs/CONTRIBUTIONS.md` daily, with the date, the work, PR links, what was AI-assisted, and any decisions.
- **Reviews:** another role reviews every pull request.
- **Pairing:** each member pairs once with another role to walk through their component. This is viva preparation.
- **AI coding tools:** they may write code, but each owner must be able to explain, change and defend it. The team owns problem framing, design, evaluation and interpretation (guide, p.17).

## Human-only tasks

These cannot be generated, and they count as done only when the named person has done them.

| Task | Who | When | Time |
|---|---|---|---|
| Assign names; start the contribution log | All | Sun 25 Oct | 30 min |
| Freeze the held-out golden subset, held-out students and attack list; record hashes | R5 | Sun 25 Oct | 2 h |
| Check held-out cases against the written policy | R1 | Mon 26 Oct | 2 h |
| Confirm the 42 card labels; write and label 45 section queries | R2 + R5 | Tue 27 – Wed 28 Oct | 4 h |
| Teacher reviews the misconception catalogue and rubric (if a teacher is available) | R1 + teacher | By Thu 29 Oct | 1–2 h |
| Write at least 10 new attacks, each with a control | R5 | By Mon 2 Nov | 3 h |
| Review lessons: accept, edit or reject, with at least one rejection and its reason | R1 (+ teacher) | Fri 6 Nov | 2 h |
| Judge labels: 30 turns, two raters | R1 + one member who does not tune agents | Fri 6 Nov | 2.5 h each |
| Teacher approves the first question sets (live) | Teacher, or R1 acting as teacher (disclosed) | Fri 6 Nov and the demo | 30 min |
| Interpret results; each member's viva | All | 9–15 Nov | — |

## If fewer than six people are active

**Four people:** combine roles as R1+R6, R2, R3 and R4+R5.

In that case the held-out freeze and the new attacks **must** be done by someone who is neither the R3 person nor the R4 person. The report states the arrangement.

**Cut list:** follow the order in [09 · Delivery](09-delivery.md#risks-and-cut-lines).

---

[← Security and privacy](06-security-and-privacy.md) · [Plan overview](README.md) · [Next: Schedule →](08-schedule.md)
