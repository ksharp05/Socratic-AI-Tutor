# Threat model · Socratic Tutor (one page)

**Owner:** R4 · Swati · **Reviewer:** R5 · **Version:** v1, 8 Nov 2026 · **Code checked:** `milestone-2` (`src/tutor/guards.py`, `toolbus.py`, `approval_token.py`)

**Scope:** the POC as built today. All guards are deterministic rule layers. The model-based layers (Prompt Guard 2, and a content-safety model replacing Llama Guard 4, which the course keys cannot reach) are not yet wired in. Users are Class 10 students (minors) and their teacher; the capstone uses simulated students only.

| # | Asset | Threats | Defences (where in code) | Remaining risk |
|---|---|---|---|---|
| 1 | **Answer keys and quiz integrity** | Student asks for answers; "I'm the teacher"; pasted homework says "print the solutions" | Input flags for key requests, role claims and injection (`guards.screen_input`); role taken from the login token, never chat; output leak check (`guards.generic_leak` + `math-tools.leak_check`); tutor role cannot call answer-bearing maths tools (`toolbus.PERMISSIONS`) | Regex misses reworded requests; leak phrases are English-only; no model-based layer yet |
| 2 | **Learner data (minors)** | Name, phone, Aadhaar typed in chat; reading another learner's record; personal data in logs; deletion ignored | PII redaction for email, Aadhaar-like numbers, Indian phones, "my name is…" (`guards.PII_PATTERNS`); learner pinning (`toolbus`); free text logged by length only (`toolbus._SCRUB`); no new records after deletion (`toolbus`, `GONE`) | Unusual formats missed (names without a cue, school, address, dashed IDs); a real pilot needs parental consent, a partner school and ethics approval (DPDP Act 2023, s.9) |
| 3 | **Teacher authority and the shared question bank** | Teacher impersonation; publishing without approval; editing after approval; concurrent publishes | HMAC token over the payload's SHA-256 and the teacher's ID: any edit voids it (`approval_token`, timing-safe compare); only the approval gate may publish, the setter only proposes (`toolbus.PERMISSIONS`); publication file lock (`toolbus`) | Signing secret falls back to a local file if `APPROVAL_SECRET` is unset; tokens never expire; public demo tokens (`dev-teacher`) must never reach a real server |
| 4 | **API keys, usage and prompts** | Key committed, pasted or screenshotted; runaway loops; long or repeated requests; prompt extraction | `.env` is git-ignored (checked: `git status` clean); `tutor check-llm` shows only the last 4 characters; 300 tool calls per session (`toolbus`); one output revision (`config/app.toml`); "reveal your prompt" flagged (`guards.INJECTION`); test-pack runner `--max-calls` cap | Budget counts tool calls, not model calls or money (no dollar cap in code); human leaks remain the main key risk; reworded prompt-extraction requests |
| 5 | **Student wellbeing** (safety, not an attack) | Distress or self-harm signals; unsuitable content shown to a child | Distress detection incl. Hinglish phrases (`guards.DISTRESS`); immediate handoff message with Tele-MANAS 14416 / 1-800-891-4416 that does not promise anyone was notified (`guards.HANDOFF_MESSAGE`) | Indirect phrasing missed; false alarms ("hopeless at maths") interrupt teaching; **no content-safety check for violence or sexual content until the guard model is added** |

**Defences that do not depend on model behaviour:** role from the signed login token; per-role tool allowlist; learner pinning; approval tied to the payload hash; length-only logging; keys outside git.

**Open items (R4):**
1. Choose and test the Llama Guard 4 replacement on clean and unsafe examples; record it in `DECISIONS.md`.
2. Wire Prompt Guard 2 as an extra injection layer, if allowed after the behaviour freeze.
3. Require `APPROVAL_SECRET` outside development.
4. Measure attack success and false blocks with defences off and on (E2, run by R5 with attacks R4 has not seen).
