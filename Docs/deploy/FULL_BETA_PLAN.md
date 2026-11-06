# Current deployment

6 November 2026: the native saved-progress beta is deployed on Vercel with Neon Free Postgres.
See [VERCEL_BETA.md](VERCEL_BETA.md) for the actual release, verification and remaining limits.
Hosted live models and R3 graph integration remain disabled/pending. The earlier preparation
plan below is historical and does not describe the deployed storage choice.

---

# Full beta deployment preparation

The user selected a full beta with saved progress. The existing Socrates beta in src/socrates_beta already has a native browser UI, signed browser ownership, SQLite sessions/cards/reviews and an integrated /beta mount in the tutor API. The stashed stateless Vercel reference preview is not this release.

## Target

Prepare one persistent Python/ASGI service serving the existing frontend and API from the same origin. Keep the runtime database, browser ownership secret, core tutor database/checkpoints and provider usage ledger on durable storage. Use one worker/instance initially because the core TutorApp serializes calls; SQLite and publication locks are not a horizontal-scaling design.

Saved progress currently belongs to a signed browser profile. This is same-browser persistence, not an account with cross-device recovery. Explain that behavior in the product and test it on mobile.

## Concrete work remaining

1. **Production transport:** configure an explicit host allowlist, secure cookies and trusted proxy handling. The current beta hardcodes localhost/127.0.0.1 and its cookie has no configurable Secure flag. Preserve same-origin mutation checks and CSP; do not disable them to make a hosted domain work.
2. **Portable content:** remove startup dependence on a local D: extraction tree by supplying a hash-pinned authorized index. Prefer a reproducible index from the committed public beta content for the initial scoped release, or a separately supplied authorized immutable artifact. Course PDFs and personal extracts are design references only and must not enter the tutor's content library or image.
3. **Honest beta publication:** define an explicit reference/machine-validated publication status for beta content. Existing assessment publication checks remain in place until that policy is implemented and tested. Do not create teacher-approved records or human reviews merely to unlock practice.
4. **Durable live-call accounting:** TeamLanguage currently keeps its call counter in memory; the ordinary LLM client also allows retries. Attach a server-side durable request/token/cost allowance, reserve before sending, preserve uncertain charges and disable automatic retries. Keep live mode off until this path is qualified. The existing USD 10 phase must allocate a bounded deployment allowance rather than let local and remote wallets independently spend the same remainder.
5. **Runtime package:** adapt the integrated container entrypoint to the platform port/durable mount and test the actual image. Docker CLI is present but the daemon was off during this assessment; no new image was built or deployed.
6. **Acceptance:** verify production startup refusal on bad configuration, owned progress across process restart, privacy deletion, index integrity, no duplicate paid requests after lost acknowledgements, private/raw-data exclusion, and the actual native UI at phone width.

R3 still owns graph integration and learner-language/diagnosis changes. This deployment work does not change those routes. Current example-service and simulator evidence is documented in ../product_quality/v3/BOUNDARY_EXAMPLES.md and SIMULATOR_SCOPE.md.

## Hosting decision after preparation

Measure the candidate's memory, disk and startup behavior before selecting a recurring plan. Confirm the exact paid host/account and monthly estimate with the user only after the runnable candidate is concrete. Provider allowance and recurring hosting charges are separate. No paid service or public link exists yet.

The ready-to-share result should be a HTTPS /beta/ link with durable progress and truthful content/review labels, not a local-only URL or a stateless demonstration.
