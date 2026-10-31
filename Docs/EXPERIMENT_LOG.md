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
