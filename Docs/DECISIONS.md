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

**To decide at the meeting on Sun 1 Nov:**
- **D-3, dates and pre-cuts:**
  - Accept the re-dated milestones in the [lead roadmap](LEAD_ROADMAP.md#timeline): M1 Mon 2, M2 Wed 4, M3 Fri 6, human day Sat 7, M4 Mon 9 Nov.
  - Cut four items now: the multi-query and rewrite ablation, Langfuse, the secondary quiz answered by the LLM, and extra seeds for E2 and E4.
- **D-4, the NCERT files** ([findings](LEAD_ROADMAP.md#what-we-found-on-31-oct)):
  - Keep one copy in `data/ncert/`, which git ignores.
  - Index chapters 4, 5 and 8 only.
  - Never index the answers appendix.
  - Leave Science unused.
  - Type 20–30 NCERT exercises as an external check set, kept out of git.
- **D-2 follow-ups:** which of Shivam and Sharath is R6, and whether the other takes R5b.

---

### D-2 · 2026-10-31 · Role names
- **Decision:**
  - Lakshya: Lead, R1 and R5. R1 is shared, with everyone contributing.
  - Rizwan: R2. Poonam: R3. Swati: R4.
  - Shivam or Sharath: R6, to confirm which.
  - The other of the two: proposed as R5b, evaluation engineer. R5b covers the judge runner, metrics, cost logging, report tables and the NCERT check set, and is the second judge rater and held-out spot-checker. Fallback: split R6 into app and platform.
- **Why:** nobody picked R5, and Lakshya holds the dataset, so Lakshya takes R5 alongside R1 ([D-1](#d-1--2026-10-30--the-lead-also-holds-r1-and-r5)). Six people fill five role slots, so the sixth takes the R5 work that needs no held-out access.
- **Evidence:** team WhatsApp group, 31 Oct; [lead roadmap](LEAD_ROADMAP.md#team).
- **Decided by:** proposed by Lakshya in the group; each person confirms at the meeting on Sun 1 Nov.

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
- **Evidence:** [separation rules](plan/07-team-and-roles.md#separation-rules); [lead roadmap](LEAD_ROADMAP.md#team).
- **Decided by:** ksharp05. The team confirms the other names and these hand-offs at the next stand-up. The evaluation report states the arrangement.
