# PR 10 review: threat model, guard-model spike S4 and D-6

**9 November 2026. Reviewer: Lakshya (Lead).** PR 10 is merged into Beta as `69556b5`. It was opened against `milestone-2`, which is an ancestor of Beta, so only Swati's three commits came in, with no conflicts. Merging records **D-6 as proposed, not confirmed.** The threat model and spike are good first versions. The items below are for Swati's refresh against Beta.

## Checked against Beta: correct as written

- `guards.py`: PII redaction (email, Aadhaar-like numbers, Indian phones, "my name is…"); distress detection; the handoff message with Tele-MANAS 14416 / 1-800-891-4416, which says the chat cannot confirm anyone was notified.
- `toolbus.py`: per-role tool allowlist, learner pinning, `GONE` after deletion, free text logged by length only (`_SCRUB`), the publication file lock, and 300 tool calls per session (`config/app.toml`).
- `approval_token.py`: an HMAC over the payload hash and teacher ID, with a timing-safe compare. It falls back to a local secret file when `APPROVAL_SECRET` is unset, and tokens never expire. The `dev-teacher` demo token is in `tutor_api/auth.py`.
- `config/app.toml`: one output revision; 25 course models, none of them a guard model; all three spike models are on the list.
- `.env` is git-ignored, and `tutor check-llm` prints only the key's last four characters.

## Out of date or missing for Beta

The threat model describes `milestone-2`. Beta also runs a public site, so these rows need updating:

- **Row 4, "no dollar cap in code": no longer true.** `tutor_eval/provider_budget.py` and `product_budget.py` cap calls and USD for scripts. The hosted site has a database-backed lease of 200 calls / USD 0.50 with a pause control (`socrates_beta/postgres_budget.py`).
- **Scope, "simulated students only": no longer true.** https://socratic-tutor-beta.vercel.app/beta/ is public. Real visitors' progress is stored in Neon Postgres under a signed browser cookie (HttpOnly, SameSite Strict, 30 days), with exact-origin and host checks and a Content-Security-Policy.
- **New asset: the hosted provider key.** It is stored encrypted in Vercel. A visitor's message goes to OpenRouter only after they consent (`model_consent`). Add rows for key exposure, consent bypass and lease exhaustion.
- **New defences to list:**
  - the live site uses a stricter, shared risk-phrase list (`guards.RISK_PATTERN`, English, Hinglish and Hindi), so "I'm hopeless at trigonometry" does not trigger it there;
  - an unsafe-chemical-guidance check on science replies (`socrates_beta/dialogue.py`);
  - deletion of a browser's data on request.
- **Remaining risk to add:** the team tutor's broader `DISTRESS` list falsely flags "I'm hopeless at trigonometry". Neither path catches violence, sexual, hate or alcohol requests; S4's unsafe cases confirm this.

## D-6: points to settle before confirming

1. **The fallback contradicts the rationale.** D-6 falls back to `anthropic/claude-haiku-5.5`, which D-5 already uses as the supervisor and planner. Yet D-6 argues the classifier should differ from the supervisor so that one model's blind spot does not cover both. Pick a fallback outside both the Haiku and Llama 3.3 roles, or argue why sharing is acceptable.
2. **Where it runs and what it costs.** Every classifier call on the live site uses the shared lease. Options:
   - classify only messages that would go to the live model;
   - put a cheap rule prefilter in front of it;
   - give it a separate small cap.

   Lakshya decides this.
3. **Fail closed is stated but not built.** The spike counts an unparsed reply as an error. The wired version must treat errors and unparsed replies as UNSAFE, parse the JSON instead of searching for a word, and get tests for both.
4. **Evidence.** The spike is 10 mild English messages, run once. It shows the approach works, not that it is robust. E2 (attacks R4 has not seen) is the real test. Lakshya builds that set.
5. There is no code freeze, so wiring it into `guards.py` is not blocked once points 1-3 are settled.

## Change made while merging

`scripts/r4/guard_model_spike.py` now runs a dry run unless given `--execute-live`. Its 30 calls bypass the project's `ProviderBudget` ledger, so it should only be run with the runner's own key. The cases, prompt and scoring are unchanged.

## Follow-ups for Swati

- [ ] Refresh `THREAT_MODEL.md` for Beta using the section above. Keep v1's history by bumping it to v2.
- [ ] Settle D-6 points 1-3, then wire the classifier with tests.
- [ ] Fix the `DISTRESS` false alarm in the team tutor's guard.
- [ ] Open future PRs against `Beta`.
