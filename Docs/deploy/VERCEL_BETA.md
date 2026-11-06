# Vercel beta

The saved-progress beta is live at **https://socratic-tutor-beta.vercel.app/beta/**.
The native browser app supports reference conversations, source citations, checked practice,
development diagnostics/self-checks, flashcards, plans and saved history. It is scoped to
Class 10 Mathematics: Quadratic Equations, Arithmetic Progressions and Introduction to Trigonometry.

Vercel Hobby serves the FastAPI application in Singapore; the connected Neon **Free**
plan stores learner profiles, conversations, assessments, observations and flashcard reviews.
No Render service or paid hosting plan was created. The previous stateless preview remains stashed.

## Current release boundary

- Hosted model generation is **disabled**. Conversations use labelled source-reading fallbacks.
  No provider key was uploaded, no new provider request was sent, and accounted development
  spend remains USD 0.14413205 / USD 10.
- This is the full native beta UI with durable progress, not the R3 connected graph.
  R3 integration remains contributor-owned and pending.
- Practice publication uses an explicitly labelled machine/reference policy: 331 practice
  items plus 12 separate development-check items are qualified against the separately
  implemented exact reference checker. Human teaching review and independent final evaluation
  remain pending. Historical approval records and frozen studies were not changed.
- Progress belongs to a signed browser cookie, valid for 30 days. The same browser can resume
  after a deployment or function replacement. Another browser/device starts a separate profile;
  there is no account-based cross-device synchronization. Clearing cookies loses access.
- Forget my data removes that profile's database rows. No claim about provider/platform backup
  retention is made.
- Real HTTPS acceptance was automated with synthetic learners. Browser visual/mobile usability
  acceptance is still pending because the computer-use surface was unavailable.

## Reproducible setup

Use the Beta checkout. Install Vercel CLI and authenticate with the owning account.
The owner's GitHub account must be connected in Vercel Login Connections; otherwise Vercel
may block CLI updates on commit-author permissions.

1. Link the intended project: `vercel link --yes --project socratic-tutor-beta --scope ksharp0508-6488`.
2. Inspect `vercel integration add neon --help`. The qualified setup uses
   `free_v3`, `region=sin1`, `auth=false`. Accept provider terms manually when requested.
   Do not duplicate an existing integration/resource or select a paid plan.
3. Confirm the connected project has `DATABASE_URL`, `TUTOR_BROWSER_SECRET`,
   `TUTOR_PUBLIC_ORIGIN=https://socratic-tutor-beta.vercel.app` and `TUTOR_BETA_LIVE=0`.
   Generate the browser secret once as 32 cryptographically random bytes encoded to 64 hex
   characters; keep the same value on subsequent releases. Never print or commit it.
4. Pull environment values only into ignored `.env.local`. Verify names, not values.
   Export `DATABASE_URL` privately into the migration shell, install the API extra, then run:
   `python -c "import os; from socrates_beta.postgres import PostgresRepository; PostgresRepository(os.environ['DATABASE_URL'], migrate=True)"`.
   Schema migration is explicit; ordinary function startup never creates or resets learner tables.
5. Run the regression suite. Real Postgres tests accept only a loopback database named
   `socrates_test`; set `BETA_TEST_POSTGRES_DSN` accordingly. CI starts its own disposable service.
6. Run `vercel deploy --dry --json` and audit every selected path. The allowlist excludes
   keys, local databases, raw experiment logs, original PDFs and private/frozen evaluation data.
   It also excludes the research pyproject from this CLI bundle so requirements.txt supplies
   the minimal native runtime. Git-triggered auto-deployment is not configured or qualified.
7. Deploy using `vercel deploy --prod --yes`. Inspect the actual ready state and aliases;
   a no-wait CLI message alone does not prove deployment success. Check the public production
   alias without a protection bypass.

Only the reconstructible public knowledge index is cached under /tmp. It is built from pinned,
committed normalized maths references, retains pending human-review flags and is checked for
integrity. Learner state and the browser secret are never placed there. A content-pack change
needs a deliberate dataset migration: do not silently discard or relabel old learner sessions.

Postgres uses parameter binding and transaction-scoped advisory ownership locks compatible
with Neon pooling. Duplicate answer submissions return the stored response and add one
checked observation. Unknown profile/session access fails closed. Cookies are Secure,
HttpOnly and SameSite Strict; POST requests enforce the configured exact origin and JSON header.
Additional hosts are exact project/deployment environment values, never a wildcard vercel.app.

## Qualification

On 6 November 2026:

- **2,537 tests passed locally**, including the actual synthetic Postgres acceptance cases.
- The initial full run had 34 fixture errors because the canonical external-corpus environment
  variable was omitted. With SOCRATES_SOURCE_WORKSPACE set to the canonical workspace all pass.
  The original failed log is retained privately.
- **18 pre-redeployment + 18 post-redeployment HTTPS checks** passed. These include native
  assets, source citations, secure cookies, rejected foreign origin, saved preferences/history/
  active practice/card review after redeployment, concurrent idempotent grading, profile
  isolation and deletion.
- The first Neon connection rejected a startup timeout option; the adapter now uses SET LOCAL
  inside the transaction. A deployment was blocked by Git-account attribution and succeeded
  after the user connected GitHub. Both failure receipts are preserved privately.
- Qualified production deployment: `dpl_GGjBBF4umEGKf4dpLKmtorUhhkwn`, Python 3.12,
  sin1, 60-second function limit, approximately 38.8 MB function output.
- Private receipts: Directions/deployment/full_beta_01. They contain synthetic acceptance
  identifiers and deployment metadata and are not published. Secrets remain private.
- Remote CI for the release commit is recorded separately after publication.

Before enabling hosted live generation, implement and qualify an atomic database-backed
provider allocation linked to the existing global USD 10 ledger, retries disabled, preserved
reservations for uncertain calls, a pause control and explicit visitor consent. The persistent-disk
DeploymentBudget helper is not safe for serverless functions and is not used by this deployment.

Official references:
[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi),
[storage integrations](https://vercel.com/docs/storage),
[Neon Marketplace](https://vercel.com/marketplace/neon),
[Git-account attribution](https://vercel.com/docs/deployments/troubleshoot-project-collaboration).
