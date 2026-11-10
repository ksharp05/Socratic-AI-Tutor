# Evaluation report: Socratic Tutor (draft skeleton)

<!-- R5 leads; each role writes its own section. 4–6 pages. Every number cites a run_id from Docs/EXPERIMENT_LOG.md.
     Tables come from `python -m tutor_eval.tables var/runs/<a> var/runs/<b> ...` and replace the placeholders below.
     No POC or development number may be quoted as a result. Final by the content freeze, Wed 11 Nov, 9 pm. -->

- **Status:** skeleton, 31 Oct 2026. Results are filled in after the held-out runs, Sat 7 – Mon 9 Nov.
- **Owners:** R5 writes data, method and results; each role writes its own section. R1 reviews the draft on Tue 10.

## 1. Problem and users (R1)

<!-- Class 10 students in India (NCERT chapters 4, 5 and 8) and their teacher. What goes wrong with answer-giving tutors;
     what "Socratic" means here, citing the teaching policy (Docs/policy/TEACHING_POLICY.md). One paragraph each. -->

## 2. The system (R3 + R6)

**How a message moves.** Every student message to the team tutor runs through one LangGraph session graph (`src/tutor/app.py`) with a SQLite checkpointer, so an interrupted turn can be resumed. Rule-based **input guards** flag distress, which goes straight to a fixed handoff message, as well as injection, answer-key requests, role claims and personal data, and they mark a student's own problem as unverified. `load_learner` reads the learner model and keeps a study plan. The **planner** is code: it picks one route from the learner's flagged misconceptions, the open question and the message. One **specialist** then runs: the diagnostician, tutor, grader or question setter, or a node that converses, refuses or hands off. Every tool call passes the **ToolBus hooks** (role allowlist, own learner only, 300 calls per session, scrubbed arguments in the trace) on its way to one of four FastMCP servers: `textbook-kb`, `math-tools`, `learner-store` and `question-bank`. Answer keys are computed by `math-tools` and never sent to the model. The **output guard** checks each draft for answer leaks and checks that every citation was actually retrieved; a failing draft is retried once, then replaced by a safe fallback. `update_memory` records misconceptions, mastery and the explanation style that worked. A language model, when one is configured, only writes the wording and may propose a diagnosis that code then verifies.

**Teacher approval gate.** The question setter can only propose. A separate approval graph solves every proposed item, waits at `interrupt()` for the teacher, and publishes only the payload whose hash the teacher approved; any edit voids the approval.

**Diagram and trace.** [ARCHITECTURE.md](ARCHITECTURE.md) has our redraw of the guide's Figure 4, coloured by role, and 12 numbered steps tied to a real 36-row trace (session `walk-1`, stub model, reproducible). It also lists where the code differs from Figure 4: routes chosen by code, rule-based guards and SQLite storage.

**Serving and operations.** Students and teachers use a Streamlit UI that talks only to a FastAPI service, which takes the role and learner from the bearer token. `docker compose up --build --wait` starts both. On 5 November the base stack was built from a fresh clone and kept its state across a restart (`Docs/m2/FRESH_INSTALL.md`). The `ops` profile adds Prometheus and a provisioned Grafana dashboard (turns, blocked leaks, denied tool calls, pending approvals, tool outcomes and latency), but that profile has not yet been run and checked. GitHub Actions runs on every pull request and on pushes to `main`, `milestone-2` and `Beta`: the portable test suite, a registry check and three gates (single-controller smoke, simulated students and security cases). A real CI failure and its fix are recorded in `Docs/ci_failure.md`. The public beta is a separate browser app (`socrates_beta`) on Vercel, with a Neon Postgres database, at https://socratic-tutor-beta.vercel.app/beta/. Its mobile and browser check is still pending.

## 2a. Safety and control (R4)

<!-- R4 owns this section. E2 numbers come from R5's run_ids; the <…> placeholders stay until then. -->

**Threat model.** `Docs/THREAT_MODEL.md` (v2, 10 Nov) covers ten assets on two surfaces: the team tutor (answer keys, learner data, the teacher's approval, keys and usage, student wellbeing) and the live beta (visitors' saved progress, consent before provider calls, the hosted key and USD 0.50 lease, live content safety, deployment secrets). Every control below is deterministic code; none relies on the tutor model behaving well.

| Control | Built (where) | Tested (how) | Still needs validation |
|---|---|---|---|
| **Input guards:** PII redaction; flags for distress, role claims, answer-key requests, injection | `guards.screen_input` | Team suite; PR #13 adds 14 tests in both directions (schoolwork wording must not flag, real distress must) | E2; indirect and Hinglish phrasing; unusual PII formats |
| **Tool hooks:** per-role allowlist, learner pinning, 300 tool calls per session, length-only logging, no records after deletion | `toolbus` | Team suite (2,103 tests on Beta) | E2 tool-result and retrieved-passage channels |
| **Approval gate:** HMAC over the payload's SHA-256 and teacher ID; any edit voids it | `approval_token` | Team suite | Required `APPROVAL_SECRET` outside development; token expiry |
| **Output guards:** retrieved-only citations; answer-leak checks, narrowed for empty-set items | `guards`, `mathcore.leak_check` (PR #12) | PR #12: 42 regression tests from the findings' phrases | Live-model replies on the 9 empty-answer items |
| **Distress handoff** with Tele-MANAS 14416, no claim that anyone was notified | `guards.DISTRESS`, `RISK_PATTERN` | 14 tests (PR #13) | A human escalation path; indirect wording |
| **Content-safety classifier** (D-6) | **Not built:** proposed only, waiting on the budget decision | Spike S4 only (below) | Lead's unseen safety set; E2 |
| **Live beta controls:** consent before provider calls; Secure, HttpOnly, SameSite=Strict cookies; profile isolation; forget-my-data; row-locked spend ledger | `socrates_beta` (`Docs/deploy/VERCEL_BETA.md`) | Lead's HTTPS checks; deletion confirmed on a synthetic profile | Guardian consent; mobile check; key expiry on 16 Nov |

**Guard-model comparison (development evidence, not a result).** Llama Guard 4 is not on the course model list, and no other dedicated guard model is. Spike S4 (`Docs/spikes/S4.md`, 9 Nov) gave three course models one six-slot SAFE/UNSAFE prompt on 10 hand-written development messages, one run each: `llama-3.1-8b-instruct` 10/10, `claude-haiku-5.5` 10/10 at about 10× the cost, and `nova-lite-v1` 9/10 (one unparseable reply). D-6 proposes Llama 3.1 8B, failing closed, with Haiku as fallback. Ten examples cannot show robustness; the classifier's real test is the Lead's safety set, which R4 has not seen, and E2.

**E2: do the defences work?** R5 ran <n> attacks (<n> original, <n> new, unseen by R4) with matching clean controls, defences off and on. run_ids: <…>.

| | Defences off | Defences on |
|---|---|---|
| Attack success | <…> | <…> |
| False blocks (controls) | <…> | <…> |
| False blocks (clean held-out sessions) | — | <…> |

<Interpretation, once the numbers are in: which channels still got through and why, the cost in false blocks, and what each layer contributed if the per-layer split was run.>

**Limitations.**
- The guards match fixed phrasings: reworded, encoded, Hinglish or multi-turn attempts can pass.
- Violent, sexual, hateful and alcohol requests are not caught on either surface until a classifier is added (finding 8).
- Citation checks verify IDs and format, not that the passage supports the claim.
- Local runs cap tool calls, not money; only the live beta has a USD cap.
- On the live site, a child's consent click is not verifiable parental consent, and provider or platform backups are outside app deletion.
- All tests above were written by the team; S4 used one run and ten examples.

**Recommended next steps.**
1. Before 16 Nov: pause the live lease, set `TUTOR_BETA_LIVE=0`, or replace the course key.
2. Decide the D-6 budget, then wire the classifier into `guards.py` behind a config switch, failing closed, with tests.
3. Add Prompt Guard 2 as a local injection layer (access is already approved).
4. Require `APPROVAL_SECRET` outside development, and expire approval tokens.
5. Before any pilot: guardian consent, a named grievance contact and human review of every distress flag.

## 3. Data (R5)

- **Source:** dataset v0.10.0, payload `49862eea…`, generated with AI assistance by one author. All review items are pending; no teacher approval yet.
- **Frozen by R5** on <date>, sampling seed <seed>, manifest `eval/HELDOUT_MANIFEST.json` (<sha256>). Held-out files stay outside git.
- **NCERT:** chapters 4, 5 and 8, Reprint 2026-27, used for retrieval only. Formulas come from teaching cards. The answers appendix is never indexed (D-4).
- **Coverage:** 13 misconceptions seeded only in held-out students; development golden cases cover 4 of 12 task families.

## 4. Method (R5)

- **Pre-registration:** `eval/PREREGISTRATION.md`, frozen <date>, SHA-256 <…>, tag `prereg-v1`. Deviations: <none / list>.
- **Simulator:** rules for all 30 misconceptions, transition rules 1–3, parameters S = 0.10, G = 0.05, T = 0.15, clearing 0.7. Validation: <result>.
- **Judge calibration:** two raters, <n> turns. Human–human κ <…>; judge κ <…> [95% CI]. Gate <passed / failed>.
- **Configurations:** E1 (c0, c1, c2; 3 seeds), E2 (defences off and on; attacks seen and new), E3 (playbook before and after; 3 seeds), E4a and E4b (1 seed). Failures and timeouts are counted.

## 5. Results (R5, with R2 for retrieval)

| Experiment | Comparison | Primary metric (95% CI) | Cost per session | run_ids |
|---|---|---|---|---|
| E1 | c2 vs c1 vs c0 | <task success> | <…> | <…> |
| E2 | defences on vs off | <attack success; false blocks> | — | <…> |
| E3 | playbook after vs before | <cleared per session; seen / unseen> | <…> | <…> |
| E4a | memory on vs off | <quiz gain> | <…> | <…> |
| E4b | hints vs telling | <leaks vs quiz gain> | <…> | <…> |

**Retrieval** (R2): Recall@5 and MRR on held-out card and section queries. Development baseline in `Docs/spikes/S3.md`, not a result.

**Judge agreement:** per-class precision and recall, from `python -m tutor_eval.agreement score`.

## 6. Lessons (R3 + R1)

**The playbook.** The Reflexion lessons are in `eval/fixtures/m3_candidate_playbook.json`: version `candidate-v1`, status `development_candidate_unreviewed`, SHA-256 `cf3f8f0f…`, recorded in `Docs/m3/BEHAVIOUR_FREEZE.json`. The four lessons were written on 5 November from two development reports (`Docs/m2/TESTPACK_RESULTS.md` and `Docs/m2/MULTITOPIC_EVALUATION.md`), and the E3 configurations load this file. There is no `playbook-v1` tag yet: the playbook is frozen only after its lessons are reviewed.

| Lesson | Scope | What it tells the tutor to do | Review |
|---|---|---|---|
| `qe-zero-factor` | Quadratic equations | When dividing might lose a zero root, ask what must be true before dividing and which factor cases still need checking | Pending |
| `ap-displacements` | Arithmetic progressions | Separate the number of terms from the number of common-difference steps; ask the learner to describe the displacement | Pending |
| `tr-reference` | Trigonometry | When a numeric error has several possible causes, ask for the reference angle and the side labels before choosing one | Pending |
| `context-step` | All three chapters | Ask one small question about the learner's own step and cite the source; never replace the step with a formula dump or the final answer | Pending |

**Accepted and rejected lessons.** None yet. The teacher review (item 2 in `Docs/m3/v3/TEAM_ACTIONS.md`) records accept, edit or reject with a reason for each lesson. Until it happens no lesson is accepted, and we do not invent a rejection to fill this section. <R1: the decision and reason for each lesson, then the reviewed playbook's version and hash.>

**Did any lesson make results worse? (Development evidence, not a result.)** In the development E3 run (48 sessions on 16 development source cards, seeds 1–3, `gpt-4.1-mini`; run_ids `m3_live_e3_budget_tranche12-20261105-041430-c0f99159f485` and `m3_live_e3_remaining4-20261105-074756-8c7792e028ac`, against C2 `m3_live_c2-20261105-040116-9c72acbd3556`), the playbook arm and C2 had identical diagnosis counts for all 17 misconceptions. So no misconception is a harmful-lesson candidate, and none improved either. Both arms had diagnosis recall 0.042 and a success proxy of 2/48. The quiz change differed by +0.021 (bootstrap 95% interval [0.000, 0.063]), but the simulator could copy post-quiz answers in these runs, so that is not a learning estimate (`Docs/m4/E3_COMPLETE_RESULTS.md`).

**What we take from it.** With diagnosis recall this low in every arm, the per-misconception tables have very few hits to compare, so "no harmful lesson" is weak evidence. Before the final E3, the lessons need their human review and a versioned playbook with its own hash, and diagnosis coverage needs to improve, because the per-misconception comparison can only judge a lesson where misconceptions are actually diagnosed.

## 7. Limitations (R5)

- **Simulated students, not real students.** Quiz gains hold only under the pre-registered rules.
- **Wide confidence intervals:** only 24 held-out students.
- **Learning is modelled by rules,** and rule 1(b) used <the judge / the code proxy>.
- **One author:** a single person wrote the dataset, the held-out cases, the 30 original attacks and the POC's agents, guards, diagnosis rules and simulator. The hand-offs are in D-1.
- **No teacher review yet** <or: what the teacher reviewed>. If R1 acted as teacher, it is stated here.
- <Anything unsupported: for example, attack channels that could not be delivered.>

## 8. What a supervised pilot with real students would need (R1 + R5)

<!-- Consent and data protection: DPDP Act 2023, every user is a child. Teacher oversight and distress escalation,
     human review of the dataset, real student error data, and an independent held-out set. -->

## Appendix: reproducing every number

`pip install -e ".[dev]"`, then each run's config from its manifest: `python -m tutor_eval.harness --config <file> --heldout`. Held-out runs need R5's private files.
