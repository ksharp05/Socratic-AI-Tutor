# Work plan: Lakshya (Lead, R1 and R5)

What Lakshya delivers as R1 (domain and product) and R5 (evaluation and red team), day by day. It also covers what Lakshya hands to each person, what Lakshya needs from them, and the decisions that still need the team.

- **Status:** draft of 31 Oct 2026, built from the course guides, the [plan](../plan/README.md), the [lead roadmap](../LEAD_ROADMAP.md) and the dataset itself.
- **Dates:** follow the roadmap. Where the plan's older dates differ, the roadmap wins.
- **Other roles:** each one can copy this layout for its own plan in `Docs/roles/`.

## 1. What I own

| Role | Deliverables | Not mine (hand-offs in [D-1](../DECISIONS.md)) |
|---|---|---|
| **R1** | Teaching and mode policy, with the answer-leak definition and the after-the-last-hint rule; teacher review of the misconception catalogue and rubric; held-out policy check; lesson-review rubric and lesson review; judge labels; question-set approval as teacher (disclosed); demo-script approval; slide outline | Refusal and safety **wording** (R4); prompts and agents (R3); diagnosis rules (R3 + R2) |
| **R5** | Held-out freeze and development split; simulator; harness and run manifests; at least 10 new attacks with controls; security runner; judge calibration (kappa); pre-registration; playbook freeze; experiments E1–E4; results tables; evaluation report (data, method, results) | Editing prompts, agents, guards or diagnosis rules |

The course's architecture guide (pp. 5–9) defines R1 as the role that "decides what the tutor teaches and what 'correct' means". It says R5's harness "uses code checks first" and calls the judge only "where code cannot decide".

## 2. Day by day

| Day | R1 | R5 | Evidence |
|---|---|---|---|
| **Sat 31 Oct** | Policy v0: structure, leak definition, hint stages | Freeze prep: sampling script, golden-set selection rules, `eval/private/` ignored by git | This plan; policy draft |
| **Sun 1 Nov** | **Teaching policy v1** to R3 and R4 by evening; book the teacher | **Held-out freeze before the meeting:** seed, record hashes, `Docs/EXPERIMENT_LOG.md`. **Development split** in `eval/dev/` | Hashes committed; `eval/dev/` merged |
| **Mon 2 · M1** | Held-out policy check with the spot-checker; teaching scenarios to R2 for section queries | Spike S6: cost of an 8-turn development session. Simulator rewrite started on the dataset kernel. Harness skeleton with `run_id` and manifest | `Docs/spikes/S6.md`; harness PR |
| **Tue 3** | Teacher reviews the catalogue and rubric (or R1 acts as teacher, disclosed). Labelled leak and non-leak examples to R4 | Simulator rules for all 30 seeded misconceptions; harness runs C1 vs C2 on 2 development cards; 45 section queries labelled with R2 | Review record; examples file; harness run |
| **Wed 4 · M2** | Run the demo script on `main`; file gaps as issues | At least 10 new attacks with controls, kept from R4; security runner; leak and diagnosis metrics (with R5b) | Attack hashes in the log; runner PR |
| **Thu 5** | Lesson-review rubric | Simulator validation: contrast test, drift check, card leaks. Pre-registration draft to R2 | Validation note; draft |
| **Fri 6 · M3** | — | **Pre-registration frozen and hashed.** Development golden run; Reflexion iteration 2 with R3; 30 turns sampled for judge labels; refreshed cost | `eval/PREREGISTRATION.md` hash in the log |
| **Sat 7 · human day** | Lesson review (at least one rejection); judge labels with the second rater, the leak label topped up to about 60 turns; approve question sets as teacher | Kappa; **playbook frozen** (`playbook-v1`); evening: E1 seed 1, E2, E3 seed 1 | Labels file; kappa; tag |
| **Sun 8** | — | E4a, E4b, deployment configuration; E1 and E3 seed 2 (with R5b) | `run_id`s in the log |
| **Mon 9 · M4** | Slide outline to R2 | E1 and E3 seed 3; results tables with spread (R5b drafts) | Tables, every number with a `run_id` |
| **Tue 10** | Review the report draft | Report draft: data, method, results | Draft |
| **Wed 11** | Demo recording with R6 | Final report. **Content freeze at 9 pm** | Final files |
| **Thu 12** | — | Final checks: no keys, PDFs or held-out data in git | Tag `v1.0`; submitted by 6 pm |

**If Sat 31 Oct – Wed 4 Nov overruns, keep this order:**
1. The held-out freeze and the development split. They block R2, R3 and every experiment.
2. The teaching policy. It blocks R3 and R4.
3. The simulator and the harness.
4. The new attacks and the judge. E2 is not until Sat 7.

## 3. What I hand over

| What | To | By | Where and in what form | Why they need it |
|---|---|---|---|---|
| **Teaching policy v1** | R3, R4, R2, R5b | Sun 1 | `Docs/policy/TEACHING_POLICY.md`: numbered, testable rules (section 5 lists them) | R3's tutor constraints and R4's leak detector and mode rules are written against it |
| **Held-out hashes and manifest** | Everyone | Sun 1 | `Docs/EXPERIMENT_LOG.md`: seed, per-record SHA-256 lists, counts. No content | Proves later that nothing changed after tuning |
| **Development split** | R2, R3, R5b | Sun 1 | `eval/dev/`: 40 golden cases, 16 students, 22 quiz pairs, 15 card queries; with hashes | Lets everyone tune and test without touching held-out data |
| **Misconception catalogue fields** | R3 + R2 | Mon 2 | `content/dataset-v0.10.0/misconceptions.jsonl`, mapped to the guide's hand-off: id, chapter, concept, probe, tell-tale sign | Their diagnosis rules are written from it, not from the simulator |
| **Teaching scenarios** | R2 | Mon 2 | 15–20 short student situations per chapter, from development cases only | R2 and R5 write the 45 section queries from them, before tuning retrieval |
| **Labelled leak examples** | R4 | Tue 3 | `eval/dev/leak_examples.jsonl`: at least 40 turns labelled leak / not leak, covering every answer kind | R4's CI gate needs detector precision and recall ≥ 0.9 |
| **Eval command, metric names, CI threshold** | R6 | Wed 4 | `tutor eval` or `python -m eval.run --config …`; names in the harness README | The guide's R5 → R6 hand-off: `eval-gate` and Grafana panels |
| **Simulator and harness** | R3, R5b | Wed 4 | `src/tutor_eval/` and `eval/` | R3's Reflexion loop needs an evaluator; R5b builds the judge and metrics on it |
| **Pre-registration** | R2 for approval | Thu 5 | `eval/PREREGISTRATION.md` | R1 and R5 are one person, so someone else approves |
| **30 sampled turns** | Second rater | Fri 6 | Development runs only, at least 5 per label class | Judge calibration on Sat 7 |
| **New attacks** | R4, **only after E2** | Sat 7 evening | Moved from `eval/private/` once E2 has run | Separation rule 2 |
| **Results tables** | R2 (slides), everyone (report) | Mon 9 | Markdown tables, every number with a `run_id` | Slides and report sections |
| **Report skeleton** | Each role | Mon 9 | 8-section outline; each role writes its own section | Report draft on Tue 10 |
| **Demo-script approval; slide outline** | R6; R2 | Mon 2; Mon 9 | Comments on R6's script PR; outline file | R6 records the demo; R2 drafts the slides |

## 4. What I need from others

| What | From | By | Blocks | If it's late |
|---|---|---|---|---|
| Comments on teaching policy v1 | R3, R4 | Mon 2 | Their M1 work; my leak examples | I freeze v1 as written and log changes as v1.1 |
| Diagnosis rules rewritten from the catalogue, without reading `src/tutor_eval/` | R3 + R2 | M1–M2 | A fair diagnosis metric | The POC rules stay, and the report says they share an author with the simulator |
| A minimal C1 (one agent, every tool) | R3 | **Wed 4**. The roadmap says M3, but the M2 exit check needs it | Harness C1 vs C2 at M2 | M2 runs C2 against the fixed workflow (C0) instead |
| C0 baseline, Reflexion loop, behaviour frozen | R3 | Fri 6 | E1, E3 | E3 is cut to one seed |
| A supervisor model on the course list, not from Google (the judge's family) and preferably not Meta (the simulator's) | R3 | Mon 2 | Deployment configuration; cost | Deployment configuration dropped (item 5 on the cut list) |
| A direct-answer prompt variant for E4b | R3 (R5 may not edit prompts) | Fri 6 | E4b | E4b dropped |
| Per-layer defence switches; leak-guard switch; a safety classifier on the course list | R4 | Wed 4 – Fri 6 | E2, E4b | E2 runs all-on vs all-off only |
| Memory on/off switch | R2 | Wed 4 | E4a | E4a dropped |
| Co-labelling of 45 section queries; approval of the pre-registration | R2 | Tue 3; Thu 5 | Retrieval metric; frozen pre-registration | — |
| Compose `eval` profile, cost and latency metrics, `eval-gate` job | R6 | Fri 6 | Running experiments from `main` | Experiments run with `tutor eval` locally |
| Judge runner, metrics, cost logging, table scripts; second rater; help with runs | R5b, or R6 if there is no R5b | M1 – Mon 9 | Most of the last week | I carry it, and the deployment configuration is cut first |
| Spot-check of 20 held-out cases against the policy | R5b, or R6 | Mon 2 | The held-out policy check | Recorded as not done |
| Two hours with a maths teacher | Teacher | Tue 3 and Sat 7 | Catalogue review, lesson review | R1 acts as teacher, disclosed in the report |
| Whether a key may be a GitHub secret; extra quota if needed | Faculty | Ask Mon 2 | `live-eval` workflow; E1 volume | Live runs from local machines only |

## 5. What the teaching policy must decide

R3 and R4 asked, through the plan, for numbered rules they can test. Policy v1 answers each question below. Each answer follows the POC unless there is a reason to change it.

1. **Modes.** What the tutor may say in practice mode and in quiz mode, and which tools each mode may call. In the POC, a quiz gives no hints and no per-item feedback.
2. **Hint stages.**
   - How many stages there are, and what each may reveal. Practice items have 3 questioning stages; misconception ladders have 2.
   - Whether a wrong attempt uses up a stage. The POC says yes, and it counts attempts but never uses them.
3. **After the last hint.** The plan: after 3 stages and 2 failed attempts, a parallel worked example on different numbers, never the active item, then mark the item for revisit. This needs an explicit exemption from the dataset's `staged_questions_only` rule.
4. **Answer leak**, per answer kind:
   - The final answer (equivalent forms included) or a worked-solution pattern, given before the student produced it.
   - Decide each edge case: one root of two, echoing the student's own answer, `boolean`, `classification`, `coefficients` and `defined_value` answers. The POC detector does not check those last four kinds, which cover 185 of the 665 items.
5. **What a tutor turn looks like:** at most one question, at most 60 words, cites what it retrieved. These are already POC prompt rules.
6. **Explanation styles.** The plan names six, but the POC uses different names; pick one list.
7. **Distress.** R1 sets the trigger and the escalation rule; R4 writes the wording and builds it. The guide gives this to R1, D-1 gives the wording to R4, and right now nobody owns the rule.
8. **Quiz items.** Where in-tutor quiz items come from. The POC uses practice items; the quiz pairs are for evaluation only.

Examples in the policy come from development cases only.

## 6. Decisions needed

My recommendation comes first in each item. Items marked **(Sun)** go on the meeting's decision sheet.

1. **Held-out files live outside the repository** (Sun). Keep them in the dataset folder on my machine and a private drive. The plan says `eval/private/`, which git does not ignore, so this branch adds it to `.gitignore` as a safety net.
2. **The 30 existing attacks** (Sun). R4 may build against them, as `06-security-and-privacy.md` and the dataset README already allow. The at least 10 new ones stay hidden until E2. E2 reports "seen" and "new" attacks separately.
3. **The dataset's generators show the held-out question templates** (Sun).
   - `src/socratic_data/tasks.py` can generate items from all 12 held-out families; the exact items need the build seed and code, which are not in the repository.
   - Rule: R3 tunes only on `eval/dev/` and never generates items from held-out families.
   - The report discloses it.
4. **Development and held-out cover different ground.**
   - Golden cases: the 160 development cases cover 4 task families and 8 concepts; the 450 held-out cases cover 12 families and all 25 concepts.
   - Misconceptions: 13 are seeded only in held-out students.
   - Report seen and unseen results separately, as the plan already asks for E3.
5. **The simulator must not import the system under test.** It now grades with `tutor.mathcore`, which belongs to R4. The rewrite uses the dataset kernel, as `05-evaluation.md` specifies.
6. **Simulator parameters** go in the pre-registration:
   - slip and guess (unspecified in the plan; 0.10 and 0.05 in the POC);
   - temperature (0.7 in the plan, 0 in the dataset's draft policy);
   - turns (8 in the plan, 6 in the POC).
7. **Who checks the simulator's transition rules.** The plan gives it to R1, but that is R5 checking R5. Move it to R2, with the pre-registration.
8. **The "targets *m*" label** decides judge acceptance (κ ≥ 0.6), but it is missing from the judge's label list. Add it.
9. **R5b and held-out data.** R5b may run held-out experiments and see their results, because R5b is neither R3 nor R4. R5b never shares them with R3 or R4.
10. **Lesson review stays on development data.** R1 also holds held-out cards, so the lesson review cites development transcripts only, like prompt reviews.
11. **Where R1's documents live.** Use `Docs/policy/` from the roadmap. The guide's names (`answer_leak_policy.md`, `distress_handoff.md`) become sections of the one policy file.
12. **Disclosures for the report.** All dataset content is AI-generated by one author, and there is no independent held-out authorship. All 2,469 review items are pending, and the rubric is a draft with no teacher approval. Retrieval labels are assistant-proposed. No benchmark, retrieval or security run has happened yet.

## 7. What outside research changes

Collected on 31 Oct. Each line is something I will adopt; the link is where it comes from.

**Judge calibration (R5)**
- **30 turns is a small sample.** With n = 30, kappa's 95% interval is roughly ±0.2. Report a bootstrap interval, and top up the leak label to about 60 turns with balanced leak and no-leak cases. This is a binary label, so it is quick. Source: [Hamel Husain, LLM-as-judge](https://hamel.dev/blog/posts/llm-judge/), who suggests 30–50 of each label.
- **Gate, to pre-register:**
  - judge against the raters' consensus, κ ≥ 0.6, and no worse than the two raters' agreement with each other;
  - κ below 0.6 is inadequate ([McHugh 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3900052/));
  - MRBench's human raters reached κ = 0.71 ([MRBench](https://arxiv.org/html/2412.09416)).
- **Judge prompt:**
  - Give the judge the reference answer, and ask for the critique before the verdict.
  - On maths grading, a reference solution cut judge failures from 14/20 to 3/20 ([MT-Bench paper](https://arxiv.org/html/2306.05685v4)).
  - Never let a model judge its own family; same-family bias is documented ([self-recognition](https://arxiv.org/abs/2404.13076v1), [preference leakage](https://arxiv.org/abs/2502.01534)). Our split already avoids it: OpenAI tutor, Google judge, Meta simulator.

**Tutor rubric and leak definition (R1)**
- **Labels:** use the MRBench dimensions and labels word for word ([MRBench](https://arxiv.org/html/2412.09416)):
  - mistake identification, mistake location, revealing the answer, providing guidance, actionability, coherence, tone, human-likeness;
  - each scored Yes / To some extent / No;
  - report both strict and lenient scores, as the [BEA 2025 shared task](https://arxiv.org/html/2507.10579v1) does.
- **Three leak levels:**
  - **Full:** the final answer or a full worked solution, before a genuine attempt.
  - **Partial:** an intermediate result or next step that should have been elicited.
  - **None.**

  Sources: the [UK DfE product safety standards](https://www.gov.uk/government/publications/generative-ai-product-safety-standards/generative-ai-product-safety-standards) and [MathTutorBench](https://arxiv.org/html/2502.18940v2).
- **Never report the leak rate alone.** Pair it with student progress: a tutor that says nothing never leaks ([LearnLM](https://arxiv.org/html/2407.12687v4)).

**Simulator (R5)**
- **Check that the error shows before tutoring.** Strong models play students as too competent ([2507.08232](https://arxiv.org/html/2507.08232v1)). Before any run, a probe must show the seeded error in at least 80% of runs.
- **Run a no-help control:** without tutoring, the student does not fix the error alone.
- **Re-inject the misconception card on every student turn** to limit persona drift ([2605.06307](https://arxiv.org/abs/2605.06307)).
- **Rate realism:** R1 rates about 10 development transcripts for realism ([2502.11678](https://arxiv.org/html/2502.11678v4)).

**Red team (R5)**
- **Try [promptfoo](https://www.promptfoo.dev/docs/red-team/configuration/) for one hour on Mon 2 as the attack runner.** It is MIT-licensed and targets an HTTP endpoint or a Python script, and it supports [OpenRouter](https://www.promptfoo.dev/docs/providers/openrouter/). It has indirect-injection, prompt-extraction and custom-policy plugins. It needs Node 22 or newer, and its grader must be switched off the default OpenAI provider. Fallback: our own security runner.
- **Map our attack channels to [OWASP LLM Top 10 2025](https://genai.owasp.org/llm-top-10/):** LLM01 prompt injection (direct; indirect through retrieved text and tool results), LLM06 excessive agency (the approval gate), LLM07 system-prompt leakage (answer keys never in prompts).

**Pre-registration (R5)**
- **Freeze before any held-out run:**
  - model IDs with the access date;
  - prompts verbatim, temperatures, seeds, token limits, timeouts and retries;
  - the judge prompt.
- **Analysis rules:** mark each hypothesis confirmatory or exploratory. Use a paired design (same student seed and misconception in every arm) and a fixed N. Disclose how many prompt iterations ran during development.
- **Lock it** with a git tag. Sources: [2606.11217](https://arxiv.org/html/2606.11217) and the [ml-preregister template](https://github.com/ml-preregister/preregistration-template).

**Safety for minors (R1 policy, R4 wording)**
- **Every user is a child in law.** Under India's DPDP Act 2023, everyone under 18 counts as a child, which covers every Class 10 student.
- **Synthetic students only.** The capstone uses only simulated students, and stores the minimum data.
- **Distress responses are tiered,** from signposting up to a teacher alert, and always point to human help ([DfE standards](https://www.gov.uk/government/publications/generative-ai-product-safety-standards/generative-ai-product-safety-standards)). Confirm the Tele-MANAS numbers (14416, 1-800-891-4416) on the official site before the demo.

## 8. Risks

| Risk | Sign | Response |
|---|---|---|
| Lead, R1 and R5 peak in the same week | No R5 pull request for a day | R5b takes the judge, metrics and tables. The deployment configuration and per-layer E2 split are cut first |
| The held-out freeze slips | No hashes by Sun 1 evening | It goes before everything else; nobody uses held-out data until it is done |
| No teacher | No date by Mon 2 | R1 acts as teacher, disclosed |
| Judge kappa below 0.6 | Sat 7 calibration | The plan's fallback: report code-checked metrics only, and give judge scores as indicative |
| Course key quota runs out | `402` or `429` errors | Ask the faculty on Mon 2; cut extra seeds per the cut list; keys expire on 16 Nov |
| Simulator too easy or drifts | Validation on Thu 5 | Fix the rules before pre-registration; never after |

## 9. Next steps (Sat 31 Oct and Sun 1 Nov)

1. **Review [teaching policy v0](../policy/TEACHING_POLICY.md)**, answer its open questions, and send v1 to R3 and R4 on Sun 1.
2. **Run the held-out freeze yourself** before the meeting. It is a human-only task, so it counts only when the named person runs it. Pick the seed yourself, and keep `--private-out` outside the repository.

   ```bash
   python -m tutor_eval.freeze --build "D:/Work/IITB/Socratic Tutor/socratic_tutor_dataset_v2/builds/v0.10.0" --seed <your seed> --private-out "D:/Work/IITB/Socratic Tutor/heldout_frozen" --dry-run
   ```

   The dry run verifies the build and prints the coverage: 12 of 12 families and 25 of 25 concepts in the 60 held-out golden cases. Then run the same command without `--dry-run`, and add `--log Docs/EXPERIMENT_LOG.md`.

   The command writes three things:
   - `eval/dev/`;
   - `eval/HELDOUT_MANIFEST.json`, which holds hashes only;
   - the log entry.

   The held-out IDs go outside git. Commit `eval/dev/`, the manifest and the log on a branch.
3. Bring sections 6 and 4 to the meeting, and record the answers in `Docs/DECISIONS.md`.
4. Mon 2: one hour trying promptfoo against the POC; decide whether it runs E2 (section 7).
