# Decision log

Every decision that changes the plan, newest first, recorded on the day it is made. The viva asks which experiment changed the design, so link the evidence: a spike note in `Docs/spikes/` or a `run_id`.

**Format:**

```
### D-<number> · YYYY-MM-DD · <short title>
- **Decision:**
- **Why:**
- **Evidence:** spike note, run_id or trace
- **Decided by:**
```

## Still open

The open decisions Q1–Q9 in the [plan overview](plan/README.md#open-decisions). Record each one here once the team settles it.

**Raised 31 Oct, from the faculty's list of models for the course keys** (in `course_models` in `config/app.toml`):
- **Two plan models are not on the list.** `openai/gpt-4.1`, the supervisor and planner model, needs a replacement chosen by R3. `meta-llama/llama-guard-4-12b`, the safety classifier, needs a replacement chosen by R4. The plan's other models are on the list: `gpt-4.1-mini`, `gemini-3.1-flash-lite` and `llama-3.3-70b-instruct`. First run `tutor check-llm --all` to confirm what the keys reach.
- **Keys are personal.** The faculty asks that no one share their key. [09 · Delivery](plan/09-delivery.md) stores one member's key as a GitHub secret for the `live-eval` workflow. Ask the faculty whether that is allowed, or run live evaluations locally.

---

### D-1 · 2026-10-30 · The Lead also holds R1 and R5
- **Decision:** ksharp05 is Lead, R1 (domain and product) and R5 (evaluation and red team).
- **Why it needs hand-offs:** the same person generated the dataset (including the held-out cases and the 30 original attacks) and wrote the proof of concept (including its agents, guards, diagnosis rules and simulator). The plan also says R1 never writes attacks.
- **Hand-offs:**
  - R3 + R2 rewrite the POC's diagnosis rules from the misconception catalogue, without reading the simulator.
  - R4 owns `guards.py` and every guard layer.
  - Refusal and safety wording in prompts is decided by R4 alone; R1's prompt reviews cover teaching only.
  - R5 never edits prompts, agents, guards or diagnosis rules.
  - R2 approves the pre-registration wording. R6 spot-checks 20 held-out cases against the teaching policy. R4 or R6 is the second judge rater.
  - Held-out files stay out of git; only their hashes are committed.
  - Drafting help: R3 checks which models the keys reach, R6 drafts the demo script, and R2 drafts the slides.
- **Evidence:** [separation rules](plan/07-team-and-roles.md#separation-rules); [lead roadmap](LEAD_ROADMAP.md#your-own-roles-lead-r1-and-r5).
- **Decided by:** ksharp05. The team confirms the other names and these hand-offs at the next stand-up. The evaluation report states the arrangement.
