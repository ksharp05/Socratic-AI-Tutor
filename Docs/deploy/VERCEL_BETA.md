# Vercel live beta

**Link:** https://socratic-tutor-beta.vercel.app/beta/

The native browser app now has opt-in live language responses from
`openai/gpt-4.1-mini` through OpenRouter, source citations, checked practice,
development checks, flashcards, plans and saved conversations.
Its supported content is Class 10 Mathematics: Quadratic Equations,
Arithmetic Progressions and Introduction to Trigonometry.
Vercel Hobby and the connected Neon Free database are in use; no Render
resource or paid hosting plan was created.

## Current behaviour and source scope

Broad questions such as “Can you tell me about trigonometry” resolve through
the scoped concept catalogue, even when the literal chapter name is absent
from the passage text. Topic-discovery questions list the actual supported
chapters. Out-of-scope queries do not invent a new subject.

The frozen normalized reference pack remains unchanged. Eight separately
versioned plain-language OpenStax-based notes provide clearer foundation
explanations and correct an incomplete legacy quadratic definition.
They have distinct citation IDs, an explicit pack hash, HTML source links and
pending human-review flags. Historical citations remain resolvable.
The notes supplement the base index; they are not a rewrite or relabeling of
frozen data. Replies record the supplement bundle version.

Quadratic definitions must retain highest-power/degree-two qualifications;
graph facts absent from the supplied excerpts fail closed to a source-reading
fallback. Citation ID/format checks are not full semantic entailment verification.
The current notes and guards improve known cases; they do not establish
independent pedagogical review or universal language correctness.

R3's connected graph remains contributor-owned and is not enabled here.
The explicit machine/reference publication policy qualifies 331 practice
items and 12 separate development-check items. No teacher approval, independent
final evaluation or learning-effectiveness result is claimed.

## Saved progress and consent

Postgres stores signed browser profiles, preferences, conversations, assessments,
observations and flashcard reviews. Progress survives function replacement
and deployments. Only reconstructible public index data is cached under /tmp.

Cookies are Secure, HttpOnly and SameSite Strict with a 30-day lifetime.
Progress belongs to that browser profile; another device/browser gets a separate
profile. Clearing cookies loses access. There is no account-based cross-device sync.
The same-origin JSON boundary, exact host allowlist, profile isolation and
forget-my-data deletion are active.

Visitors must explicitly consent before chat reaches OpenRouter. Consent can be
withdrawn in Learning preferences; subsequent model chat is rejected.
Preferences do not clear an existing conversation unless class/subject changes.
A distressed message uses the immediate local safety response without provider use.
Provider/platform backup retention is not represented as application deletion.

## Durable provider allowance

The user specifically approved storing the existing provider key in Vercel's
encrypted production environment and sending consenting visitor chat, redacted
recent conversation and short public maths references to OpenRouter.

The active hosted lease is **200 provider requests and USD 0.50**, reserved
inside the existing USD 10 product-phase ceiling, not added to it.
Every Vercel instance shares one Postgres row-lock ledger. Reservations are
committed before network use; calls, conservative cost and unknown outcomes
survive cold starts. Automatic SDK retries are disabled. One bounded format
repair, when needed, is a separate counted request. Exact paid-payload replay,
missing/changed grants and unprovisioned wallets fail closed.

A trusted operator can pause with `PostgresBudget.set_paused(True)`.
The lease cannot also spend through a local PhaseWallet, and generic phase close
cannot release its still-active cap. Existing phase allocations/wallets remain
unchanged. Before further allocation/closure, pause and reconcile the remote
ledger; do not reset or silently renew the lease.

At the recorded development checkpoint: **USD 0.15739205 accounted / USD 10**;
22 hosted attempts, USD 0.01326 provider-reported, no unknown reserved call.
Usage can increase as consenting visitors use the site. The full USD 0.50 lease
remains reserved while it is active. Current authoritative receipts stay private
under Directions/deployment/live_chat_02; synchronize before quoting later totals.

### Key replaced on 11 November 2026

The first hosted key, the course OpenRouter key, reached its USD 5 limit on
10 November. On 11 November the user supplied a new OpenRouter key. It went
into Vercel's encrypted production setting `LLM_API_KEY` and production was
redeployed (`dpl_AyuhwAar2LLcsHPLxt5FAHwgzsUm`, then `dpl_5HKwSso4nSMSaRy89EpSLrewUdto`
with the forget fix). The new key has a **USD 5 limit**, and OpenRouter
lists it as expiring on **9 February 2027**. The 200-request lease is unchanged:
86 requests were used at the 11 November sync.

**The key's account has no purchased credits.** OpenRouter's `/credits` shows
`total_credits: 0`. After about USD 0.21 of use on 11 November it refused calls
with 402 "Insufficient credits". The key's USD 5 limit is a cap, not a balance.
Until someone adds credits to that OpenRouter account, live replies fall back to
labelled source reading. This was checked on production after the 402 started.

When a key runs out or expires, provider calls fail. Each chat reply then falls back to a
labelled source-reading response (`provider_failed_source_fallback` in
`src/socrates_beta/dialogue.py`), so the site keeps working without live replies.
Reservations are committed before each network call, so expect failed attempts
to keep counting toward the 200-request lease.

Neither `/health` nor `/beta/api/health` will show the problem: both report the
configured `TUTOR_BETA_LIVE` setting, not whether the key still works.

Before the key's limit or expiry, choose one of these:

- pause the lease with `PostgresBudget.set_paused(True)`;
- set `TUTOR_BETA_LIVE=0` and redeploy;
- replace the key with another approved one.

Course keys are personal, and the course tracks usage per key
([decisions](../DECISIONS.md)).

No API key, local learner database, raw experiment log, private/frozen evaluation
material or original course PDF is in GitHub. The deployed source allowlist
excludes them too. Keys belong only in Vercel encrypted environment settings.

## Qualification

The saved-progress baseline passed 2,537 local tests, 18 pre- and 18 post-
redeployment HTTPS checks, and successful exact-source CI
[42256373547](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42256373547).
Direct DB checks confirmed complete deletion of the synthetic profile.

This iteration passed **2,564 full local tests**, including hosted/local reuse
protections. Exact-source [CI 42263327146](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42263327146)
passes on be36b8c: 2,530 portable tests, two registry checks and all three
smoke gates; 34 external-corpus cases pass locally. All 142 deployed source
files match this published code. Receipts are recorded in VERCEL_QUALIFICATION.json.
Node syntax checks pass for the consent/citation UI.

The exact screenshot conversation passes publicly. The initial 12-turn live
smoke passed format, citation-ID and consent/safety controls, but assistant
review found weak source/definition behaviour; those results are retained and
are not reclassified as semantic successes. After versioned notes and stronger
guards, all eight targeted live questions passed; their source notes opened
correctly and synthetic learner data was deleted. These are development checks
by the same assistant, not independently authored final assessment.

Actual browser/mobile visual acceptance is still pending: the computer-use
surface failed to initialize. Automated real HTTPS checks and mobile viewport
metadata do not substitute for that review.

## Deployment operations

Use the Beta checkout and owning Vercel account. Link project
`socratic-tutor-beta` under `ksharp0508-6488`. Its owner's GitHub login must be
connected; this resolved the observed Git-author deployment block.

First bootstrap with live generation off. Verify environment key names
(`DATABASE_URL`, `TUTOR_BROWSER_SECRET`, `TUTOR_PUBLIC_ORIGIN`, `TUTOR_BETA_LIVE`)
after linking the existing Neon Free integration. Never print secret values or
duplicate resources. The browser secret is 32 random bytes encoded to 64 hex
characters and must remain stable across deployments.

Schema setup is explicit with `PostgresRepository(..., migrate=True)`;
function startup never creates or resets learner tables.
**Schema version 2 (11 Nov, saved-question queue)** only adds the `revisit_queue` table and its index; no
existing rows change, and migrating twice is harmless. **Order: deploy first, then migrate.** The new code
runs on a version-1 database with saved questions switched off, so a routine deploy without the migration is
safe. Then run the migration and saved questions switch on at the next cold start. Never migrate while
version-1 code is still serving: it refuses a version-2 database.
Live activation additionally requires the explicitly approved, pre-funded grant,
`PostgresBudget.provision`, model/key settings and visitor consent.
Do not use the file-based DeploymentBudget in serverless functions.

Run `vercel deploy --dry --json`, audit its exact public runtime file list,
then `vercel deploy --prod --yes`. The allowlist selects the minimal
requirements.txt runtime and excludes the research pyproject.
Git-triggered automatic deployments are not configured or qualified.
Inspect READY status and the anonymous production alias; no-wait CLI text alone
does not prove success. Data and provider ledger persist across deployments.

[FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi),
[storage](https://vercel.com/docs/storage),
[Neon Free integration](https://vercel.com/marketplace/neon),
[quadratic definitions](https://openstax.org/books/college-algebra-2e/pages/2-5-quadratic-equations),
[right-triangle ratios](https://openstax.org/books/precalculus-2e/pages/5-4-right-triangle-trigonometry),
[arithmetic sequences](https://openstax.org/books/college-algebra-2e/pages/9-2-arithmetic-sequences).
