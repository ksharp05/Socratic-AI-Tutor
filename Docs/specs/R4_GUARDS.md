# Spec for R4 (Swati): tools, control and security

What the guard and tool layer must do by M2 (Wed 4 Nov) and M3 (Fri 6 Nov) so E2 and E4b can run. Written by the Lead (Lakshya). Under D-1, R4 owns every guard layer and all refusal and safety wording.

**Your files:** `src/tutor/mcp_servers/` (with R2 for `textbook_kb.py`), `toolbus.py`, `approval_token.py`, `guards.py`, `mathcore.py` (except the diagnosis rules, which are R3 + R2's). Work on branches named `r4/<topic>`.

**Write your detector from the policy, not from the evaluation's code.** Don't copy `src/tutor_eval/leakcheck.py`. If the guard and the measurement were the same code, E2 and E4b would grade themselves.

## Must have by M2 (Wed 4 Nov)

| # | Requirement | Acceptance |
|---|---|---|
| 1 | **Full-leak detector for all six answer kinds** (TP-L1): `finite_set` (one root of two counts as partial), empty set, `scalar`, `boolean`, `classification`, `coefficients`, `defined_value`. Today only `finite_set` and `scalar` are checked; the rest cover 185 of 665 items | Precision and recall ≥ 0.9 on R1's 40 labelled turns (due Tue 3) |
| 2 | **Leak check on the student's own problem** (TP-M4), when it can be parsed | A test |
| 3 | **Quiz mode** (TP-M2, TP-L): no hints or explanations, the tutor isn't called, and per-item correctness is never revealed before the end | A test; the security case `maintain_quiz_mode` holds |
| 4 | **Distress tiers** (TP-D1–D4): Tier 1 acknowledges stress, Tier 2 hands off at once and alerts the teacher, fail closed. Your wording. Confirm the Tele-MANAS numbers on the official site | The distress security case holds |
| 5 | **A safety classifier on the course key list** to replace Llama Guard 4 (spike S4) | `Docs/spikes/S4.md`, with what it blocks and its latency |

## Must have by M3 (Fri 6 Nov)

| # | Requirement | Acceptance |
|---|---|---|
| 6 | **Per-layer switches for E2.** `TutorApp(defences=...)` also accepts a dict of layers, for example `{"input_screen": true, "injection": true, "output_leak": true, "citations": true}`. `true` / `false` keep working | `harness` and `security` run with a layer turned off |
| 7 | **Injection hooks for two channels** the security runner can't reach yet: plant a passage for one session (`retrieved_passage`, with R2), and plant a tool result (`tool_result`) | `security.py` stops counting those channels as unsupported. The Lead adds the delivery code once your hook exists |
| 8 | **Parallel worked example** (TP-A2): math tools generate a same-structure item with a different answer and verify its steps; R3 calls it | A test per supported task family |
| 9 | **Leak-guard switch** for E4b `direct_answers` (with R3) | `arm = "direct_answers"` runs |
| 10 | **Threat model, one page** (`Docs/plan/06` outline); R5 reviews it | Merged |

## Rules for you

- **The new E2 attacks are kept from you until E2 has run** (separation rule 2). You may build against the 30 existing attacks and the development examples in `eval/fixtures/security_smoke.jsonl`.
- **CI runs the development security cases as a gate** (`--gate`). Keep it green.
- **Use live calls sparingly:** develop with `TUTOR_LLM=stub`, and cap any live run.
