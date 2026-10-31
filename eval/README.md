# Evaluation pipeline

How we measure the tutor (R5). Simulated students with planted misconceptions talk to one configuration of the tutor. Code scores everything it can, a calibrated LLM judge scores the rest, and every number traces back to a `run_id`.

**Everything runs offline on development data today.** Held-out runs wait for the frozen pre-registration (Fri 6 Nov).

## The pipeline

```text
eval/dev/ (development split)        eval/configs/<name>.toml
            │                                  │
            ▼                                  ▼
  simulator ──turns──► tutor arm (arms.py) ──► harness ──► var/runs/<run_id>/
  (kernel + buggy rules)   c2 today             │          manifest.json  sessions.jsonl  report.md
                                                ├─► leak checker (policy TP-L1/L2) on every turn
                                                ├─► metrics: diagnosis, leaks, quiz gain, cost, latency
                                                └─► judge.py (LLM, needs a key) ─► judge.jsonl
                                                       └─► agreement.py: human labels → kappa gate
security.py ── attack and control cases ──► tutor ──► attack success and false blocks, by channel
tables.py   ── several runs ──► one comparison table for the report
```

## Commands

Run every command from the repository root, with the environment active.

| To do this | Run |
|---|---|
| Smoke-test the pipeline, as CI does | `tutor eval`, or `python -m tutor_eval.harness --config eval/configs/dev_smoke.toml` |
| Run a configuration and log it | `python -m tutor_eval.harness --config eval/configs/<name>.toml --log Docs/EXPERIMENT_LOG.md` |
| Judge a run's turns (needs a key) | `python -m tutor_eval.judge --run var/runs/<run_id>` |
| Sample turns for the human raters | `python -m tutor_eval.agreement sample --run var/runs/<run_id> --n 30 --out var/labels/sample.csv` |
| Score rater and judge agreement | `python -m tutor_eval.agreement score --raters a.csv b.csv --judge var/runs/<run_id>/judge.jsonl --label leak` |
| Run security cases | `python -m tutor_eval.security --cases <attacks.jsonl> <controls.jsonl> [--no-defences]` |
| Compare runs in one table | `python -m tutor_eval.tables var/runs/<a> var/runs/<b>` |
| Freeze the held-out sets (once, R5) | `python -m tutor_eval.freeze ...`, see [the work plan](../Docs/roles/R1_R5_WORK_PLAN.md#9-next-steps-sat-31-oct-and-sun-1-nov) |

## What each part does

| File | Role |
|---|---|
| `src/tutor_eval/simulator.py` | The simulated student. It answers with the dataset kernel and its own buggy rules, never with tutor code. **Every one of the 30 misconceptions has a rule.** On an item of its concept that its rule doesn't fit, the student gives a generic wrong answer. Transition rules 1–3 and the parameters are in the [pre-registration](PREREGISTRATION.md) |
| Simulator voice | `voice = "template"` (default, offline) or `"llm"` in a run config: Llama phrases the opener and beliefs; answers stay exact; fallbacks are counted in the manifest. `eval/configs/dev_live.toml` tries it with a key |
| `src/tutor_eval/validate_sim.py` | Simulator validation on the 16 development cards: expression before tutoring, persistence without help, clearing only when named and targeted, no card text in messages. `python -m tutor_eval.validate_sim` (after the freeze) |
| `src/tutor_eval/harness.py` | Runs the sessions: pre-quiz, up to 8 tutor turns, post-quiz. Checks every tutor turn for leaks against the problem on screen, the student's own problem and the post-quiz items. Counts failures and timeouts (over 120 s), and writes the manifest with config, code and data hashes |
| `src/tutor_eval/leakcheck.py` | The policy's leak definition as code: full or partial, for all six answer kinds. It is separate from R4's guard; it measures and never blocks |
| `src/tutor_eval/metrics.py`, `tables.py` | Diagnosis recall, precision and macro-F1; full and partial leaks; quiz gain with a bootstrap 95% CI; task success; tool calls; latency p50/p95; cost; spread across seeds |
| `src/tutor_eval/judge.py`, `agreement.py` | MRBench labels, plus the leak level and "targets *m*". Cohen's and quadratic-weighted kappa with bootstrap CIs. The gate: κ ≥ 0.6, and no worse than the two raters' agreement |
| `src/tutor_eval/security.py` | Attack and control cases in the dataset's format. Planted-passage and tool-result channels, and teacher-context cases, are counted as unsupported until the hooks exist |
| `eval/configs/` | One file per run configuration. `dev_smoke.toml` is the CI gate |
| `eval/fixtures/security_smoke.jsonl` | Development security examples only. New attacks stay outside the repository until E2 |

## What other roles plug in

The evaluation never writes the system it measures, because separation rule 3 and D-1 forbid it. So each arm and switch is built by its owner, behind the interface in `src/tutor_eval/arms.py`:

| Needed for | What | Owner | Interface |
|---|---|---|---|
| E1 | `c1`: one agent with every tool, the same middleware and budget | R3 · Poonam | `make_app("c1", ...)` returns an object with `turn(session_id, learner_id, text, mode)` returning `reply`, `route`, `diagnosis`, `active_item`, `checks`, `tools` (as `TutorApp.turn` does) |
| E1 | `c0`: fixed workflow (guard → retrieve → one hint prompt → guard) | R3 · Poonam | Same |
| E2 | Per-layer defence switches | R4 · Swati | A `defences` value that names layers, e.g. `{"input": true, "output_leak": false}`, accepted by `TutorApp` |
| E2 | Injection hooks for the `retrieved_passage` and `tool_result` channels | R4 + R2 | A way to plant a passage or a tool result for one session, so `security.py` can deliver those cases |
| E4a | `memory_off`: no learner model, static plan | R2 · Rizwan | `make_app("memory_off", ...)` |
| E4b | `direct_answers`: the tutor may answer, leak guard off | R3 + R4 | `make_app("direct_answers", ...)` |
| Judge | A calibrated "targets *m*" label replaces the code proxy in rule 1(b) | R5 + raters | `judge.jsonl` |
| Cost | `usage.cost` from OpenRouter, so cost is measured, not estimated from token prices | R3 (`llm.py`) | A `cost_usd` field in the `llm` trace event |

## Rules

- **Development data only, until the pre-registration is frozen.** The harness refuses held-out data unless `--heldout` is given and `eval/PREREGISTRATION.md` says `**Status:** frozen`.
- **Nothing is dropped.** Errors and timeouts stay in every denominator. Unscorable answers count as items, but not as correct.
- **Every number in the report has a `run_id`**, and every run is in `Docs/EXPERIMENT_LOG.md`.
- **POC and development numbers are smoke tests, never results.**
