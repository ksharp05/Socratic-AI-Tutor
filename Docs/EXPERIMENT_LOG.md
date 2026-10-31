# Experiment log

Every evaluation run, newest last, failed runs included. R5 owns this file; anyone who runs an experiment adds its entry the same day. The report quotes only numbers that trace back to a `run_id` here.

**Format:**

```
### YYYY-MM-DD · <run_id> · <purpose>
- **Config:** file and SHA-256; model IDs; seed
- **Data:** development or held-out, and which sets
- **Outcome:** what happened, failures and timeouts counted
- **Decision:** what changes because of it, with a link to Docs/DECISIONS.md if any
```

**Rules:**
- **No held-out data here, ever:** only hashes, counts and run IDs. Held-out files and IDs stay outside git (R5).
- **The held-out freeze is the first entry.** It is written by `python -m tutor_eval.freeze ... --log Docs/EXPERIMENT_LOG.md` when R5 runs the freeze ([how](roles/R1_R5_WORK_PLAN.md#9-next-steps-sat-31-oct-and-sun-1-nov)).
- **A change to a frozen set after held-out results is a deviation.** Log it, move the affected cases to development, and say so in the report.

---

### 2026-10-31 · s6_cost-20261031-212818 · Spike S6: live cost of development sessions
- **Config:** `eval/configs/s6_cost.toml` (`7a3e081277a4`); arm c2, defences on; tutor `openai/gpt-4.1-mini`; student voice `meta-llama/llama-3.3-70b-instruct`; seeds 1, 2, 3; budget 40 calls / USD 0.15
- **Data:** development (POC cards `sim_v2_010`, `sim_v2_013`); 6 sessions, 48 turns
- **Outcome:** 0 failures; 0 tutor model calls (the POC's hint and grading paths are templates); 6 voice calls, 0 fallbacks, 2 of 6 openers dropped the equation; no leaks; not a result
- **Decision:** the voice must keep the equation (fixed); no further live tutor runs until R3's agents call the model. See [S6](spikes/S6.md)

### 2026-10-31 · s6_cost-20261031-212818/judge · Judge on 40 development turns
- **Config:** `src/tutor_eval/judge.py`; `google/gemini-3.1-flash-lite`, temperature 0; `--limit 40`
- **Data:** development; 40 turns of the run above
- **Outcome:** 40 labelled, 0 failed; leak "none" on all 40, matching the code checker; about USD 0.015 (estimated); labels not yet calibrated
- **Decision:** judge tokens are now logged; judge whole runs only for reported experiments
