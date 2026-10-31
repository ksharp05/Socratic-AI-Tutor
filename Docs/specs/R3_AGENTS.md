# Spec for R3 (Poonam): agents and orchestration

What the tutor's agent layer must do by M2 (Wed 4 Nov) and M3 (Fri 6 Nov) so the experiments can run. Written by the Lead (Lakshya). Under D-1, R3 writes all prompts and agents; nobody else does.

**Your files:** `src/tutor/app.py` (session graph), `prompts.py`, `llm.py`, and the planner part of `learner.py`. Work on branches named `r3/<topic>`, and merge through pull requests.

## Why this is urgent

Spike S6 ([Docs/spikes/S6.md](../spikes/S6.md)) found that **the POC tutor made 0 model calls in 48 live turns**. Only the misconception tutor path and the diagnosis call the model; hints and grading feedback are templates. So until the specialists call the model, E1 compares templates and the cost estimate is empty.

## Must have by M2 (Wed 4 Nov)

| # | Requirement | Acceptance |
|---|---|---|
| 1 | **Specialists on the course model.** The tutor, diagnostician and question setter run as `create_agent` agents, or equivalent, with the MCP tools. Every tutor-route turn calls the model; code still decides grading, keys, mastery, planning and permissions | Run `python -m tutor_eval.harness --config eval/configs/dev_live.toml` (capped at USD 0.10). The manifest shows `tutor_llm_calls` > 0 on tutor-route turns, 0 failures, 0 full leaks |
| 2 | **Teaching policy rules** from [TEACHING_POLICY.md](../policy/TEACHING_POLICY.md): the student's own problem counts as an active item (TP-M4); hint stages are questions and advance per TP-H3; after a wrong attempt, one targeted question and never the value (TP-H4); turn shape TP-T1–T5; one style from the policy's list of six (map the POC names) | Your tests, plus `tutor eval` (offline) keeps passing its gate |
| 3 | **Diagnosis rules with R2 (Rizwan),** rewritten from the misconception catalogue (`content/dataset-v0.10.0/misconceptions.jsonl`). **Don't open `src/tutor_eval/`**: the simulator must not shape them | Tests from the catalogue's `example_wrong_work` and `distinguishing_evidence`, written by you and R2 |
| 4 | **A supervisor model on the course list** to replace `openai/gpt-4.1`. Not Google (the judge's family), and preferably not Meta (the simulator's). Run `tutor check-llm --all` first, about 25 small calls | Recorded in `Docs/DECISIONS.md`, with the check output |
| 5 | **Cost from OpenRouter.** Request usage accounting, and put `usage.cost` into the `llm` trace event as `detail.cost_usd` | A live run's trace has `cost_usd` on every `llm` event |

## Must have by M3 (Fri 6 Nov)

| # | Requirement | Acceptance |
|---|---|---|
| 6 | **Arm `c1`:** one agent with every tool, the same middleware and budget. It must be callable as `arms.make_app("c1", ...)` and return the same `turn()` dict as `TutorApp.turn` (`reply`, `route`, `diagnosis`, `active_item`, `checks`, `tools`) | `python -m tutor_eval.harness` with `arm = "c1"` runs `dev_smoke` with 0 failures |
| 7 | **Arm `c0`:** fixed workflow (guard → retrieve → one six-slot hint prompt → guard), no agent decisions | Same, with `arm = "c0"` |
| 8 | **After the last hint (TP-A1–A3):** a parallel worked example, generated and verified by R4's math tools, then the item is marked for revisit | A test that triggers it after 3 stages and 2 wrong attempts |
| 9 | **The Reflexion loop** (E3): candidate lessons from development runs only, in the lesson schema; iterations on Thu 5 and Fri 6 with R5 | Lessons file for R1's review on Sat 7 |
| 10 | **Arm `direct_answers`** (E4b), with R4: a prompt variant that may give answers, with the leak guard off | `arm = "direct_answers"` runs `dev_smoke` |

## Rules for you

- **Never open held-out files or results** (separation rule 1). Tune only on `eval/dev/` and `eval/poc/`.
- **Don't generate items from the held-out task families** with `socratic_data.tasks`. R5's work plan, decision 3, explains why.
- **Use live calls sparingly.** Develop with `TUTOR_LLM=stub`; every live config has a `[budget]` ([eval/README.md](../../eval/README.md#api-use)).
- **Arms are measured by R5.** The interface is fixed in `src/tutor_eval/arms.py`; tell the Lead if you need it changed.
