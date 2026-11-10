# Threat model · Socratic Tutor

**Owner:** R4 · Swati · **Reviewer:** R5 · **Version:** v2, 10 Nov 2026 (v1: 8 Nov, milestone-2)
**Checked against:** Beta code (`src/tutor/guards.py`, `toolbus.py`, `approval_token.py`, `mathcore.py`) and the live site as described in `Docs/deploy/VERCEL_BETA.md`.

**Scope.** Two surfaces. (1) The **team tutor** (TutorApp), run locally and in experiments with simulated students. (2) The **live beta** at socratic-tutor-beta.vercel.app: real anonymous visitors, likely Class 10 students and so minors, using its own practice flow (`socrates_beta`) with Postgres storage and a hosted model key. Guards in both are deterministic rule layers. The model-based safety classifier (D-6) is not wired in yet.

## Part A · Team tutor

| # | Asset | Threats | Defences (where in code) | Remaining risk |
|---|---|---|---|---|
| 1 | **Answer keys and quiz integrity** | Student asks for answers; "I'm the teacher"; pasted homework says "print the solutions" | Flags for key requests, role claims and injection (`guards.screen_input`); role from the login token, never chat; output leak checks (`guards.generic_leak`, `mathcore.leak_check`, narrowed in PR #12 so ordinary hints pass); the tutor role cannot call answer-bearing tools (`toolbus.PERMISSIONS`) | Regex misses reworded requests; leak phrases are English-only |
| 2 | **Learner data (minors)** | Name, phone, Aadhaar in chat; reading another learner; personal data in logs; deletion ignored | PII redaction (`guards.PII_PATTERNS`); learner pinning (`toolbus`); free text logged by length only (`toolbus._SCRUB`); no new records after deletion (`GONE`, HTTP 410) | Unusual formats missed (names without a cue, school, address, dashed IDs) |
| 3 | **Teacher authority and the shared question bank** | Impersonation; publishing without approval; editing after approval; concurrent publishes | HMAC token over the payload's SHA-256 and teacher ID, any edit voids it (`approval_token`); only the approval gate publishes (`toolbus.PERMISSIONS`); publication file lock | Signing secret falls back to a local file if `APPROVAL_SECRET` is unset; tokens never expire; demo tokens are public |
| 4 | **API keys, usage and prompts** | Key committed or screenshotted; runaway loops; prompt extraction | `.env` git-ignored; `tutor check-llm` shows the last 4 characters only; 300 tool calls per session; one output revision; "reveal your prompt" flagged | Local runs have a tool-call budget but no money cap; human leaks remain the main key risk |
| 5 | **Student wellbeing** | Distress or self-harm signals; unsuitable content | `guards.DISTRESS` plus the shared `RISK_PATTERN` (English, Hinglish, Hindi script); immediate handoff with Tele-MANAS 14416 / 1-800-891-4416 that does not claim anyone was notified. PR #13 stops "hopeless at `<subject>`" triggering it | Indirect phrasing missed; **violent, sexual, hateful and alcohol requests are not caught** (finding 8) until a classifier is added |

## Part B · Live beta (new in v2)

| # | Asset | Threats | Defences (per `VERCEL_BETA.md`) | Remaining risk |
|---|---|---|---|---|
| 6 | **Visitors' saved progress in Postgres** (profiles, preferences, conversations, assessments, flashcard reviews) | One visitor reading another's data; cross-site requests; data kept after a deletion request | Signed browser profiles; cookies Secure, HttpOnly, SameSite=Strict, 30 days; same-origin JSON boundary; exact host allowlist; profile isolation; forget-my-data deletion (checked on a synthetic profile) | Anyone using the same browser sees that profile; provider and platform backups are outside app deletion; no accounts, so no recovery after clearing cookies |
| 7 | **Visitor consent and data sent to OpenRouter** | Chat sent to a third party without agreement | Explicit consent before any model call, withdrawable in preferences; recent conversation redacted before sending; distress handled locally with no provider call | A child's click is not verifiable parental consent (DPDP Act 2023, s.9); provider retention is outside our control |
| 8 | **Hosted key and money** (lease: 200 requests, USD 0.50, inside a USD 10 ceiling) | Key exposure; spend beyond the cap; parallel instances double-spending; key expiry | Key only in Vercel's encrypted environment; one Postgres row-lock ledger shared by all instances; reservations committed before network use; SDK retries off; missing or changed grants fail closed; operator pause | **Key expires 16 Nov 2026**: health checks will not show it, and failed attempts still count against the lease. Any consenting visitor can use up the lease (replies then fall back to source reading). It is one member's personal course key, so usage is attributed to them |
| 9 | **Content safety on the live chat** | Unsafe or off-topic requests from real visitors | Beta uses `RISK_PATTERN` only, with no false alarm on "hopeless at trig"; citation ID and format checks | Violence, sexual, hate and alcohol requests are not caught; citation checks are not semantic; a classifier call per message would draw on the 200-request lease |
| 10 | **Deployment and secrets** | Secrets or private data shipped; wrong code deployed | Deployed source allowlist excludes keys, the learner DB, private evaluation material and PDFs; dry-run file audit before deploy; secrets never printed; stable `TUTOR_BROWSER_SECRET` | Manual deploys from one owner account; browser and mobile visual acceptance still pending |

**Defences that do not depend on model behaviour:** role from the login token; per-role tool allowlist; learner pinning and profile isolation; approval tied to the payload hash; length-only logging; keys outside git; the row-locked spend ledger; fail-closed grants.

## Open items (R4)

1. **Before 16 Nov:** pause the lease, set `TUTOR_BETA_LIVE=0`, or swap the key (Lead's decision).
2. **D-6 classifier on the live site:** choose a budget option — a rule prefilter, classifying live chat only, or a separate small cap (Lead's decision).
3. Require `APPROVAL_SECRET` outside development; consider expiring approval tokens.
4. **E2** (R5's attack set, which R4 has not seen): attack success and false blocks with defences off and on.
5. Before any pilot with real students: guardian consent, a named grievance contact and a human review path for distress flags.
