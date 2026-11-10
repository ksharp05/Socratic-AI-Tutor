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

<!-- One-paragraph tour: guards → planner → specialists → MCP tools behind permission hooks → output guards → memory.
     The teacher-approval gate. Refer to the architecture diagram and the numbered walkthrough of one real trace. -->

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
