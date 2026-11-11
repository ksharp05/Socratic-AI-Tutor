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
### D-7 · 2026-11-11 · Safety classifier: google/gemma-4-31b-it behind the phrase screens (replaces D-6) · confirmed 12 Nov
- **Decision:** `google/gemma-4-31b-it`, with the security test's v4 classifier prompt, replaces `meta-llama/llama-3.1-8b-instruct` (D-6) as the model-based safety classifier. It sits behind the deterministic phrase screens in `src/socrates_beta/safety.py`, which answer crisis, abuse and secrecy messages with fixed text and need no model. Fail closed as in D-6. Not yet wired into `guards.py` or the beta: it needs a working key (the course key reached its USD 5 limit on 10 Nov).
- **Why:**
  - Crisis messages are where a miss is worst. On the 174-scenario quality probes, Gemma 4 31B caught 8 of 8 crisis messages; Llama 3.1 8B caught 5 of 8, which rules it out whatever its price.
  - Gemma matched the expected category on 161 of 174 messages (Llama 130), flagged 2 of 91 safe learning messages as harmful (Llama 6), and gave no unreadable output (Llama 6).
  - In the hardened front door it routed 401 of 420 attack cases acceptably, including 40 of 40 crisis and 18 of 18 child-safety cases, and 62 of 62 independently written research phrases.
  - Cost is still small: about USD 0.05 per 1,000 messages, median 0.9 s.
  - What changed the design: spike S4 used 10 hand-written examples and one run, and both Llama and Haiku scored 10/10. The larger, independently written probe and attack sets separated them. S4 stays as the record of the first choice.
- **Evidence:** the quality and safety plan, section 11 (batch `v4-judge-classify-01`, 10 Nov), and the security test report, "Safety classifier" (batch `v4-sec-05`, 10 Nov), both by R5; raw runs private in `Directions/product_quality/v4/`. Development evidence from AI judges, not teacher review. The eight-model sweep on the attack set did not run before the key ran out (about USD 0.40 to re-run).
- **Decided by:** Lakshya (R5) recommended; Swati (R4) adopted it. **Confirmed by the Lead (Lakshya) on 12 Nov 2026** after the comparison on the public core, in the Lead's words: "Yes, confirm D-7". The classifier stays switched off (`safety_classifier = "off"`) until its false-block rate comes down. Turning it on is a separate change, with tests and an E2 re-run.
- **Evidence update, 12 Nov.** On the 4,000-message held-out core of the public test set (independently labelled), Gemma 4 31B caught 68/88 crisis and child-safety messages and 83% of harmful messages, with 1 unreadable reply. It also wrongly blocked 18% of safe messages. Haiku 5.5 caught 71/88 (77% harmful, 34 unreadable, scored on 3,021 messages); GPT-5 nano caught 64/88 (286 unreadable); Llama 3.1 8B caught 10/88 (845 unreadable). The fixed screens alone caught 27/88. See `Docs/testing/PUBLIC_TESTSET.md` and batches v4-d7-01 to 03.

### D-6 · 2026-11-09 · Safety classifier: meta-llama/llama-3.1-8b-instruct (proposed; replaced by D-7)
- **Decision:** `meta-llama/llama-3.1-8b-instruct` replaces `meta-llama/llama-guard-4-12b` (not on the course list; no dedicated guard model is) as the content-safety classifier, with a six-slot SAFE/UNSAFE prompt. Fallback: `anthropic/claude-haiku-5.5`. Fail closed: an error or unparseable reply counts as UNSAFE. Not yet wired into `guards.py`: behaviour was frozen on 6 Nov, so the Lead decides whether it goes in before E2.
- **Why:**
  - Tied best in the spike: 10/10, no false blocks on tricky safe messages ("this quadratic is killing me") and no misses. Claude Haiku 5.5 also scored 10/10; Nova Lite 9/10 (one unparseable reply).
  - About 10× cheaper than Haiku ($0.00005 vs $0.00050 for 10 checks), and the check runs on every message.
  - Same family as Llama Guard (its base model), as the plan's substitution rule asks, and a different model from the supervisor ([D-5](#d-5--2026-11-03--supervisor-model-anthropicclaude-haiku-55-provisional)), so one model's blind spot does not cover both.
  - Trade-offs: slower (median 1.8 s vs 1.1 s), and the same family as the student simulator (Llama 3.3 70B).
- **Evidence:** [spike S4](spikes/S4.md); `scripts/r4/guard_model_spike.py`, run on 9 Nov 2026. 10 development examples, one run: a sanity check, not a robustness result; E2 is the real test.
- **Decided by:** Swati (R4), proposed; Lead to confirm in review.

### D-5 · 2026-11-03 · Supervisor model: anthropic/claude-haiku-5.5 (provisional)

- **Decision:** `anthropic/claude-haiku-5.5` replaces `openai/gpt-4.1` (not on the course list) as the supervisor and planner model. Fallback: `openai/gpt-6-luna`. Provisional until the first `dev_live` run with agent specialists (R3 item 1) confirms its routing.
- **Why:**
  - Not Google (the judge's family) and not Meta (the simulator's).
  - Fast and short: 1.06 s and 4 output tokens on the check. Reasoning-heavy models (gpt-5-mini, qwen3.7-plus, glm-5.3-flash) spent 40–230 hidden tokens on a one-word reply, which costs money and time on every turn.
  - $0.10 in / $0.50 out per million tokens, a twentieth of gpt-4.1's price ($2 / $8). OpenRouter lists tool-calling support.
  - The fallback gpt-6-luna has the same price but was slower (2.4 s).
- **Also found:** `anthropic/claude-3-haiku` was retired on 10 Sep 2026 (404); it should come off `course_models`.
- **Evidence:** `tutor check-llm --all` on 3 Nov 2026 (below); prices from OpenRouter's model list the same day.
- **Decided by:** Poonam (R3), proposed; Lead to confirm in review.

```
Base URL: https://openrouter.ai/api/v1
Model:    openai/gpt-4.1-mini
  openai/gpt-6-luna … ok in 2433 ms, replied 'ready' (tokens 13 in, 5 out)
  openai/gpt-5-mini … ok in 13741 ms, replied 'ready' (tokens 13 in, 42 out)
  openai/gpt-5-nano … ok in 2185 ms, replied 'ready' (tokens 13 in, 143 out)
  openai/gpt-5.4-nano … ok in 9194 ms, replied 'ready' (tokens 13 in, 5 out)
  openai/gpt-4.1-mini … ok in 7884 ms, replied 'ready' (tokens 14 in, 2 out)
  openai/gpt-4.1-nano … ok in 3749 ms, replied 'ready' (tokens 14 in, 2 out)
  openai/gpt-4o-mini … ok in 1123 ms, replied 'ready' (tokens 14 in, 1 out)
  openai/gpt-oss-120b … ok in 1437 ms, replied 'ready' (tokens 74 in, 51 out)
  anthropic/claude-haiku-5.5 … ok in 1064 ms, replied 'ready' (tokens 18 in, 4 out)
  anthropic/claude-3-haiku … FAILED: this key cannot reach this model; use one from course_models in config/app.toml (OpenAIModelNotFoundError: Error code: 404 - Claude 3 Haiku was deprecated on Sep 10, 2026. We recommend migrating to Claude Haiku 4.5 (openrouter.ai/anthropic/claude-haiku-4.5).)
  google/gemini-3.1-flash-lite … ok in 650 ms, replied 'ready' (tokens 7 in, 1 out)
  google/gemma-4-31b-it … ok in 381 ms, replied 'ready' (tokens 20 in, 2 out)
  qwen/qwen3.7-plus … ok in 5284 ms, replied 'ready' (tokens 17 in, 230 out)
  qwen/qwen3.6-plus … ok in 3050 ms, replied 'ready' (tokens 17 in, 124 out)
  qwen/qwen3.8-27b … ok in 447 ms, replied 'ready' (tokens 59 in, 22 out)
  qwen/qwen3.5-35b-a3b … ok in 2671 ms, replied 'ready' (tokens 17 in, 145 out)
  qwen/qwen3.5-9b … ok in 3969 ms, replied 'ready' (tokens 17 in, 138 out)
  deepseek/deepseek-v4-flash … ok in 397 ms, replied 'ready' (tokens 11 in, 2 out)
  deepseek/deepseek-chat … ok in 1359 ms, replied 'Ready' (tokens 10 in, 2 out)
  z-ai/glm-5.3 … ok in 439 ms, replied 'ready' (tokens 19 in, 3 out)
  z-ai/glm-5.3-flash … ok in 7823 ms, replied 'ready' (tokens 19 in, 89 out)
  meta-llama/llama-3.3-70b-instruct … ok in 904 ms, replied 'ready' (tokens 17 in, 2 out)
  meta-llama/llama-3.1-70b-instruct … ok in 461 ms, replied 'Ready' (tokens 17 in, 2 out)
  meta-llama/llama-3.1-8b-instruct … ok in 560 ms, replied 'Ready' (tokens 17 in, 2 out)
  amazon/nova-lite-v1 … ok in 905 ms, replied 'Ready' (tokens 7 in, 2 out)
24 of 25 models answered.
```

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
