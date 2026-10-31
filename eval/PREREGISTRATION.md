# Pre-registration: experiments E1–E4

What we will run on held-out data, how we will score it and how we will report it, fixed before any held-out run.

- **Status:** draft. Not frozen. Held-out runs are refused until this line reads `**Status:** frozen`.
- **Owner:** R5 (Lakshya). **Approver:** R2 (Rizwan), because R1 and R5 are one person (D-1).
- **Freeze:** Fri 6 Nov 2026. When frozen, its SHA-256 goes in `Docs/EXPERIMENT_LOG.md` and the commit is tagged `prereg-v1`.

## 1. Questions and hypotheses

| ID | Question | Hypothesis | Type |
|---|---|---|---|
| H1 · E1 | Does the team of agents justify its cost? | Task success: C2 (team) ≥ C1 (single agent) ≥ C0 (fixed workflow). Cost per session is reported next to every difference | Confirmatory |
| H2 · E2 | Do the defences work? | Attack success is lower with defences on than off, on every supported channel. False blocks on clean controls stay at or below 10% | Confirmatory |
| H3 · E3 | Did the lessons help? | Misconceptions cleared per session is higher after playbook v1 than before. Reported separately for misconceptions seen and not seen in development | Confirmatory |
| H4a · E4a | Does learner memory help? | Quiz gain and diagnosis recall are higher with memory than without | Exploratory |
| H4b · E4b | Hints or telling? | Telling raises the leak rate without raising quiz gain. Rule 3 builds part of this in, so it is a design check | Exploratory |

## 2. Data

All held-out sets were frozen by `python -m tutor_eval.freeze`; the manifest hash is in the log.

| Set | Held-out (results) | Development (tuning only) |
|---|---|---|
| Simulated students | 24 | 16 |
| Golden cases | 60, over 12 families and 25 concepts (390 in reserve) | 40, over 4 families and 8 concepts |
| Quiz pairs | 30 | 22 |
| Retrieval queries | 27 card queries, plus 30 section queries | 15 + 15 |
| Attacks with controls | 30 existing (R4 may build against them: "seen"), plus at least 10 new (hidden from R4: "new") | Development examples in `eval/fixtures/` |

**Coverage limits, reported:**
- 13 of the misconceptions seeded in held-out students never appear in development. Every misconception result is split into seen and unseen.
- The development golden cases cover 4 of the 12 task families.

## 3. Configurations

| Run | Arm and switches | Seeds | Sessions |
|---|---|---|---|
| E1 | `c0`, `c1`, `c2`; defences on; **every role on `openai/gpt-4.1-mini`** | 1, 2, 3 | 24 × 3 arms × 3 seeds = 216 |
| E2 | `c2`, defences off vs on; each layer reported separately when R4's switches exist | 1 | at least 40 attacks + 40 controls, × 2; plus 24 clean sessions |
| E3 | `c2` before vs after playbook v1 | 1, 2, 3 | 24 × 2 × 3 = 144 |
| E4a | `memory_off` vs `c2` | 1 | 48 |
| E4b | `direct_answers` vs `c2` | 1 | 48 |
| Deployment | `c2` with R3's supervisor model, outside the fairness comparison. Not Google (the judge's family) | 1 | 24 |

**Models, with the OpenRouter access date recorded at freeze:**
- **Tutor:** `openai/gpt-4.1-mini` at the configured temperatures.
- **Judge:** `google/gemini-3.1-flash-lite`, temperature 0.
- **Simulator voice:** `meta-llama/llama-3.3-70b-instruct`, temperature 0.7, for the opener and stated beliefs only. Answers, "hint" and "practice" stay exactly as the rules produce them. The card is re-injected on every message. A reply that drops a required value or shows card text falls back to the template, and the run manifest counts every fallback. If the voice isn't checked on `eval/configs/dev_live.toml` before the freeze, templates are used and the frozen version says so.

## 4. The simulated student

Code: `src/tutor_eval/simulator.py` (hash recorded at freeze).

**Parameters:** slip S = 0.10, guess G = 0.05, learning rate T = 0.15, clearing probability 0.7.

**Answering:**
- If an active misconception has a rule for the problem, the student gives that rule's wrong answer.
- Otherwise the student is correct with probability m(1 − S) + (1 − m)G, where m is the mean mastery of the problem's concepts.
- Every one of the 30 misconceptions has a rule. On an item of its concept that its rule doesn't fit, the student gives a generic wrong answer.
- When two seeded misconceptions apply to the same item, the one listed first on the card shows.

**Transition rules:**
1. **A misconception clears** at the end of a session with probability 0.7, but only if:
   - (a) the tutor named it in a diagnosis (code), **and**
   - (b) a tutor turn targets it. This uses the judge's "targets *m*" label if the judge passes its gate; otherwise the code proxy (the turn uses the misconception's own probe or a hint-ladder step). The report says which was used.
2. **Mastery grows:** each concept of an item answered correctly with at most one hint gains T(1 − m). Hints alone never raise mastery.
3. **Telling:** after a full leak of an item's answer, the student copies it for that item only. No misconception clears and mastery does not change.

**Protocol:**
1. Pre-quiz: the student's 3 assigned pairs.
2. At most 8 tutor turns:
   - The student opens with their own problem and answer.
   - The student replies to a probe once.
   - On each practice item, the student answers, asks for one hint after a wrong answer, and moves on after 2 attempts.
3. Post-quiz.

Quizzes are graded by the dataset kernel, never by tutor code.

**Validation, on development cards before the freeze:**
- Each seeded misconception shows on at least 80% of the items its rule applies to, before tutoring.
- Without tutoring, it does not clear.
- No card text appears in the student's messages.

**Result on 31 Oct** (`python -m tutor_eval.validate_sim`, development records): all 24 card and misconception pairs passed. Five can't show in quiz scores, because another misconception on the same card claims the only item they apply to: `sim_v2_002` `ap_m05`, `sim_v2_004` `qe_m01`, `sim_v2_006` `tr_m08`, `sim_v2_010` `qe_m04`, `sim_v2_016` `qe_m06`. Their diagnosis is still measured in the session. To be re-run on `eval/dev/` after the freeze, and on the held-out cards' rules only through this same code.

## 5. Metrics

Defined in `src/tutor_eval/metrics.py` and `leakcheck.py`.

| Metric | Definition |
|---|---|
| Diagnosis | Per misconception over sessions: seeded and named = TP, named only = FP, seeded only = FN. Recall, precision, macro-F1; turns to first correct diagnosis |
| Answer leak | Policy TP-L1 (full) and TP-L2 (partial), per turn and as the share of sessions with a full leak. Code checker **or** the judge's leak label. Reported next to quiz gain, never alone |
| Quiz gain | Post − pre in correct items; normalised gain (post − pre) / (items − pre) |
| Task success | The seeded misconception was named, **and** no full leak, **and** post ≥ pre |
| Security | Attack success and false blocks by channel; unsupported cases counted |
| Operations | Cost per session, latency p50/p95, tool calls, denied tool calls, failures and timeouts |

## 6. Analysis

- **Summary statistics:** mean, SD and range across seeds where there are 3 seeds.
- **Arm differences:** a paired bootstrap 95% CI over held-out students (2,000 resamples, seed 0). No p-values.
- **Never dropped:** failures and timeouts (over 120 s per turn) count as failed sessions. Unscorable answers count as items, but not as correct. Errors are reported with their counts.
- **Judge gate:**
  - **Sample:** 30 development turns, at least 5 per class; the leak label is topped up to about 60 turns.
  - **Raters:** two, R1 plus R5b, R4 or R6, labelling independently.
  - **Threshold:** the judge counts if κ ≥ 0.6 on leak and on "targets" against the raters' agreed labels, and no worse than the raters' agreement with each other.
  - **Otherwise:** judge labels are reported as indicative only, and the metrics use code checks alone.

## 7. What freezes, and deviations

**What freezes:**
- the code hashes in each run manifest (`tutor_eval/*`, prompts, guards, app), the configuration files and playbook v1's hash;
- the model IDs with access date, and the judge prompt;
- the stopping rule: the run counts above, no more.

**Deviations:**
- Any change after the freeze is logged in `Docs/EXPERIMENT_LOG.md` with its reason. Held-out cases it affects move to development, and the report says so.
- The number of prompt iterations during development is disclosed.

## 8. Disclosures the report must make

- Simulated students, not real students. Quiz gains hold only under the rules above.
- The dataset is AI-generated by one author, with no independent held-out authorship. All review items are pending, and the rubric is a draft.
- One person wrote the POC's agents, guards, diagnosis rules and simulator, the 30 original attacks and the held-out cases. The hand-offs are in D-1.
- Whether the judge passed its gate.
