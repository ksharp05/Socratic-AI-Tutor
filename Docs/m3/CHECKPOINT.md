# Current checkpoint - security test (USD 5 programme); course key exhausted

**10 November 2026, later.** The user asked for much more research and many more runs for the security test, with a
USD 5 cap ("you can spend a total of 5 dollars to complete the security test as this is one of the most important
thing"). The report is the Claude Doc "Socratic Tutor security test report"
(https://claude.ai/artifact/NmTTPrkjTGYfRbSjf62WVz). The quality plan doc now points to it and has its DPDP date corrected.

Headline: on a 420-case attack set (14 families, 18 jailbreak wrappers, English/Hindi/Hinglish), the live beta fails
118 cases (28%); a hardened front-door prototype (v4) fails 10 (4 strict), none judged severe, and misses no crisis or
abuse message on the strict measure.
- The live beta missed 61/63 crisis and abuse cases and 36/37 independently written research phrases.
- It turned a sleeping-pill question into an AP exercise, and promised a child "I won't tell anyone".
- No pipeline gave step-by-step harmful instructions, and the canary never leaked in 3,776 replies.
- A fresh adaptive round against v4 succeeded 6/64 (3 strict).
- The offline app review found no XSS. Its two high findings are a maths-checker CPU stall (37-character answer) and a
  distress-screen bypass by whitespace or Unicode. The review is private in
  `Directions/product_quality/v4/security/appsec_review.md` (exploit details).

New code:
- `eval/fixtures/security_attacks_v1.py` (420 cases), `security_research_phrases_v1.py` (62) and
  `security_phonetic_v1.py` (28, not yet run).
- `scripts/qa/{security_run,security_judge,security_summary,security_checks,security_adaptive,
  security_classifier_sweep,hardened_front_door}.py`.
- `live_probe_run.py allocate --program security`: a programme cap read from
  `Directions/product_quality/v4/programs/security.json`.
- 16 new tests. CI test set: 2,654 passed, 7 skipped, 34 deselected.

**The course OpenRouter key is exhausted.** OpenRouter `/key` shows a USD 5 total limit with USD 5.005 used; it expires
on 16 Nov.
- Batch v4-sec-06 hit "403 Key limit exceeded".
- The live Vercel beta uses the same key, so its live chat is refused until the course raises the limit or issues a new key.
- Security spend: provider-reported USD 3.2292 (it matches OpenRouter's daily usage); ledger USD 3.7767, because the 28
  refused calls are booked at their reserved maximum.
- Six batches, all sealed. Phase accounted USD 5.2080 of 10.
- Not run: the classifier sweep, the phonetic set, the Gemini tutor run, and part of the judging (about USD 0.80).

DPDP correction: the children's provisions (s.9, Rule 10) start on 13 May 2027. The 13 Nov 2026 date was only an
un-notified proposal.

Next: the fix plan in the report. Fixes 2-7 need no model or key:
- port the normaliser, crisis and abuse screens and three-language templates into `socrates_beta.dialogue`;
- no secrecy promises;
- the answer-check fix;
- a 2 s limit on the maths checker;
- accurate privacy wording.

Nothing is pushed or deployed. Decisions pending with the user: a key (limit raise or new key) before the viva on
15 Nov; approval to port the deterministic layers; and D-6 (Gemma 4 31B with the v4 classifier prompt).

---

# Checkpoint - quality and safety plan with ledgered live tests

**10 November 2026.** The user asked for researched improvements to language, tone, topics, out-of-context guardrails,
foul language, system prompts and the pipeline, and authorized the remaining USD 10 phase for testing. The plan is the
Claude Doc "Socratic Tutor quality and safety plan" (https://claude.ai/artifact/BYPB9xB5vvhpCatA3bc7oV), with an
appendix tab listing the 174 probe scenarios and the prototype prompts. Headline: with the same model (GPT-4.1-mini), a
front-door classifier plus policy replies and prompt v3 raised AI-judged acceptable replies from 16% to 52% of the 174
scenarios and cut unsafe verdicts from 7 to 1. The judges were Claude Haiku 5.5 and Gemini 3.1 Flash Lite, which agreed on
76-88% of verdicts; this is development evidence, not human or teacher review.

New tools: `eval/fixtures/quality_safety_probes_v1.py` and `scripts/qa/{live_probe_run,router_prototype,judge_probe_run,
classifier_probe_run,summarise_runs}.py`. `tutor_eval.product_budget.ProductPhase` gains an opt-in `iteration='v4'` that
allows one local batch beside the running hosted lease; the hosted USD 0.50 cap stays reserved and untouched (7 new tests).
The v4 authorization is `Directions/product_quality/v4/ITERATION_AUTHORIZATION.json`, which records the user's approval
quote and verified prices. Five v4 batches are sealed: 5,959 calls, USD 1.2373. Phase accounted spend is USD 1.4313 of 10,
and USD 8.1186 is unallocated. Raw runs and judgements are under `Directions/product_quality/v4/runs/` (private).

Key findings:
- Claude Haiku 5.5 and Qwen 3.7 Plus return empty text under small caps unless `reasoning.enabled=false` is sent. This
  affects D-5.
- Gemma 4 31B is the best safety classifier: 161/174 exact, 8/8 crisis. The D-6 candidate Llama 3.1 8B missed 3 of 8
  crisis messages.
- Gemini 3.1 Flash Lite is best for Hindi and Hinglish teaching. GPT-4.1-mini is the safest for policy replies.

Nothing is pushed or deployed. Decisions pending with the user: a model key after 16 Nov, a DPDP check (a reported
proposal for 13 Nov 2026 is unverified), and replacing the D-6 classifier.

---

# Current checkpoint - R3 PRs 7-9 merged locally, findings and fix plan

**9 November 2026.** Local Beta merges R3's PRs 7 (worked example after the last hint), 8 (saved revisit
marks) and 9 ('there is no such term') as `383b261` and `831c06a`. **Not pushed and not redeployed**; the live site still
runs be36b8c. Full local suite: **2,665 passed, 7 skipped**. Offline stub-model stress runs over all 331 practice items,
restart/revisit scenarios and a 36-phrase answer matrix are in `scripts/qa/`. Results, nine shortcomings and the proposed
fix order are in **Docs/m3/PR7_9_TEST_FINDINGS.md**. The top issue predates these PRs: the live beta grades "empty set"
and similar answers wrong on the 9 term-count items that tell students to use an empty set.
The user confirmed there is **no code freeze**; BEHAVIOUR_FREEZE.json only pins the code behind the M3 study results.
PR 10 (Swati, R4: threat model, guard-model spike S4, proposed D-6) is merged into Beta as `69556b5`; **D-6 stays
proposed**. Beta gaps in the threat model, D-6 points to settle (its Haiku fallback duplicates D-5's supervisor model)
and her follow-ups are in **Docs/m3/PR10_REVIEW.md**. The spike script now dry-runs unless given `--execute-live`,
because its 30 calls bypass the ProviderBudget ledger. Owners for all follow-ups are in PR7_9_TEST_FINDINGS.md.
No provider calls were made; the hosted lease and phase spend are unchanged.

---

# Current checkpoint - live Vercel beta and topic/source fixes

**6 November 2026.** Continue Beta in Main with canonical D: cwd. The live native beta is at
**https://socratic-tutor-beta.vercel.app/beta/** on Vercel Hobby + Neon Free. The user-reported
trigonometry opening and topic-discovery failures are fixed and verified on the public site.
User explicitly approved encrypted production key storage, OpenRouter payload transfer for
consenting visitors, and a **200-request / USD 0.50 hosted lease inside the USD 10 phase**.
Published code is **be36b8c1e701c3aa28e68cc8e1dcd328799ceb11**. The short release note and all verified changes are on Beta.

Start with Docs/deploy/VERCEL_BETA.md, VERCEL_QUALIFICATION.json and
Docs/releases/2026-11-06-beta.md. **2,564 full local tests pass** on this release.
Real Postgres concurrency, cap, pause, unknown-outcome, no-reset, profile isolation, consent,
deletion and local/hosted double-spend protections pass. JS syntax checks pass.
The saved-progress baseline also passed 36 HTTPS checks across a real redeployment and
GitHub CI 42256373547 on b2e2038 (2,503 portable + two registry + three smoke gates).
Current [CI 42263327146](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42263327146) is successful on be36b8c: 2,530 portable tests, two registry checks and all three smoke gates. All 142 deployed source files match this code.

Live development smoke: 12 initial replies accepted format/citation checks; assistant review
found weak quadratic/source explanations, retained honestly. Eight targeted post-fix live
questions then passed with correct source notes. These are same-assistant development checks,
not independent final assessment, teacher review or learning evidence.
Eight new immutable-version public OpenStax-based notes supplement the unchanged frozen
reference pack. Distinct citation IDs and pack hashes preserve old source access and identify
the current teaching material. Definitions require highest-power/degree-two qualifications;
unsupported graph claims fail closed. Reference-note citations open HTML sections, not fake PDF pages.

Latest deployed release: dpl_GPVxmXTLwLtMybFFDX9KvY6MP7CZ, READY, Python3.12 in sin1.
Signed browser ownership and all learner state live in Postgres with a stable Vercel secret.
The public index alone is cached under /tmp. Progress is per browser cookie (30 days), not
an account shared across devices. No Render resource or paid hosting plan exists.
The old stateless Vercel preview stash remains preserved. Actual browser/mobile visual acceptance
is pending because the computer-use surface failed; automated HTTPS checks are not a substitute.

**Accounted phase spend USD 0.15739205 / USD 10** at the latest sync:
22 hosted attempts, USD 0.01326 provider-reported, no unknown reserved call.
Prior 1,218 historical/current attempts remain preserved; cumulative known count is 1,240.
The active lease hosted-vercel-live-02 remains RUNNING with its USD0.50 cap reserved.
All old wallets remain closed/unchanged. Do not repeat paid acceptance scripts, reset the DB
ledger, spend the same allocation locally, release its cap or create another phase batch.
First run Directions/deployment/live_chat_02/sync_hosted_usage.py before later accounting.
A trusted operator can pause the DB lease; generic close/reuse is deliberately blocked.
Remote close/rotation needs dedicated pause/reconciliation tooling and is not automated.

Private grants, credentials, raw outputs/logs, synthetic cookies and receipts stay under
Directions/deployment/live_chat_02; none are in GitHub or deployment source uploads.
Source pack/course PDFs/frozen studies/tags/human review forms remain preserved.
R3 graph integration remains contributor-owned and pending; no competing R3 pipeline was added.
Reference/machine practice publication is explicit (331 practice + 12 development-check items);
formal M3/M4 independent/human acceptance remains separate.

Vercel CLI65.12.1, the official global plugin and shared MCP OAuth are configured.
Native MCP doc-search/list-teams checks still need a chat tool reload; actual CLI team access
and deployment are verified. The old one-time quota-reset automation completed and was deleted;
no automatic future restart is currently scheduled.

Release code, CI and deployment are verified. Next: mobile/browser usability acceptance
and broader independent source/learner evaluation. R3's contributor integrates graph work.

---

# Current checkpoint - saved-progress beta deployed on Vercel

**6 November 2026.** Continue Beta in Main with canonical D: cwd. Published release source:
**b2e2038139da29b428c8a7e1040d9b9b9d4e7d30**. Public link:
**https://socratic-tutor-beta.vercel.app/beta/**. Vercel Hobby + Neon free_v3 in Singapore
serve the existing native UI with durable Postgres learner progress. No Render resource or paid
hosting plan was created. The old stateless preview stash remains preserved.

Start with Docs/deploy/VERCEL_BETA.md and VERCEL_QUALIFICATION.json. **2,537 full local tests pass**,
including real loopback Postgres acceptance. The first full run omitted the canonical external-corpus
environment variable and had 34 fixture errors; its log is preserved. The corrected full run passes.
**18 pre-redeployment + 18 post-redeployment HTTPS checks pass**: preferences, conversations,
active practice and flashcard reviews survive a real Vercel redeployment; concurrent duplicate
grading is idempotent, another browser profile cannot read the session, and forgetting deletes
all synthetic owned rows, confirmed directly in Postgres. All 138 files returned in Vercel's
authenticated deployed-source manifest match the published runtime bytes. Private receipts,
initial failures, raw logs, synthetic cookies and credentials stay under Directions/deployment/full_beta_01.
GitHub CI [42256373547](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42256373547) is successful on b2e2038: 2,503 portable tests, 34 corpus cases excluded, two registry checks and all three smoke gates. A user-reported broad-topic defect is now fixed on the live site; the subsequent live-chat budget candidate is under verification.

The cloud uses a stable secret from Vercel and an explicit database migration. Only the rebuildable
public reference index is cached under /tmp. Browser ownership cookies are Secure, HttpOnly and
SameSite Strict; exact-origin and host checks are active. Human approval flags were not fabricated:
the explicitly labelled reference/machine policy qualifies 331 practice items plus 12 separate
development-check items. This is not teacher review, independent final authorship or efficacy evidence.

**Hosted live models are disabled; no provider key was uploaded or request sent.** Conversations
use labelled source-reading fallbacks. The persistent-disk budget helper is not used by serverless
functions. Before hosted generation, implement and qualify an atomic database-backed grant tied
to the existing global USD 10 ledger, disable retries, preserve uncertain reservations, add a pause
control and obtain any required explicit hosted payload/destination approval plus visitor consent.
R3 connected-graph integration remains contributor-owned/pending; no competing R3 pipeline was added.

Saved progress belongs to this browser cookie, not a cross-device account; another browser/device
starts a separate profile. Actual browser visual/mobile usability acceptance remains pending because
the computer-use tool failed to initialize. The public HTTPS link works without Vercel login.
The Git-author deployment block was resolved after the user connected their GitHub account in Vercel.

Vercel CLI65.12.1, the official global Vercel plugin and shared MCP OAuth are configured.
Native MCP documentation-search/list-teams checks remain pending a chat tool reload; CLI team
inspection and actual deployment are verified. Do not claim those MCP tools were invoked.

Provider accounting is unchanged: 1,218 total attempts, phase reported USD 0.09403805,
**accounted USD 0.14413205 / USD 10**, remaining USD 9.85586795. All original wallets remain
closed and unchanged; no new allocation or duplicate experiment was started. Frozen studies,
reports, tags, private data, original course PDFs and blank human reviews are preserved.
Publication is authorized. The old one-time resumption automation completed and was deleted;
no automatic future restart is currently scheduled.

Next: finish the release CI receipt, then qualify mobile/browser usability and the durable hosted
provider budget if continuing the live beta. R3's contributor integrates the graph services.
Formal M3/M4 independent/human acceptance remains separate.

---

# Current checkpoint - case-preserving examples and simulator protocol

**6 November 2026.** Continue Beta in Main; cwd canonical D:. Latest published code is **dd309a7f00a34aa259d35435bb907be475ef8d06**. **2,173 local full four-suite tests pass** (387 focused example/case checks, 336 protocol checks). GitHub CI [42241832120](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42241832120) is successful on that exact source: 2,139 portable tests, two synthetic registry tests and all three smoke gates pass; 34 external-corpus cases pass locally. Private ACTIVE_CONTINUATION.json identifies any active work; do not start duplicate qualification, baseline or provider jobs.

Start with Docs/product_quality/v3/BOUNDARY_EXAMPLES.md/json, SIMULATOR_SCOPE.md/json and TOOLS_HANDOFF.md. Service parallel-example-v3 preserves its declared case signature and enforces the separate exact-reference checker. Public coverage is 316 checked examples/331 eligible items; 15 deliberately return unavailable where preservation shares an invariant active answer. A new 900-distinct-input synthetic audit gives 782 verified examples/118 safe fallbacks, no case/independent-answer/guard failures, and rejects all 782 appended-text mutations. This is not matched difficulty, teacher review, independent final data or learning evidence. V2 clarity ratings remain historical and must not be transferred.

The opt-in public-practice-protocol-v2 preserves legacy typed answers/RNG/rules and uses explicit AP-count language. Mathematical reference support is already 331/331; canonical parser roundtrip changes 322/331 to 331/331. A cached C2 audit isolates all 18 unchecked attempts to “there is no such term” routed as tutor. The natural learner phrase remains an R3 language gap; canonical formatting does not fix free-form product understanding. Legacy simulator and run_session are unchanged; no new C1/C2 study was run.

R3 still owns example/revisit graph integration, fresh-message diagnosis and input-language fixes. No R3 code or supervisor switch was made. New reports are service/preflight evidence only. Original studies, frozen data/tags, blank human forms and closed wallets are preserved. The first reversed-index guard failure, before source, protocol, scripts, exact source hashes, raw audits and local logs are private under Directions/product_quality/v3/boundary_examples_01 and simulator_scope_01.

Next priority is the chosen **full beta with saved progress**. The existing Socrates beta already supplies a native browser UI, signed browser ownership and SQLite progress behind /beta; do not substitute the stashed stateless Vercel preview or assume a new frontend is required. Deployment readiness still needs configurable production hosts/secure cookies/proxy origin handling, a portable authorised index, honest machine/reference beta publication policy, durable server-side provider caps and restart/mobile acceptance. Existing TeamLanguage call count resets in memory; the ordinary LLM path also permits retries. Do not expose live calls under the USD 10 allowance before durable accounting is attached. Docker CLI is installed but the daemon was off at inspection; no image/deployment was started in this continuation. Exact recurring hosting/account approval remains separate from provider allowance.

Accounted provider spend is unchanged **USD 0.14413205 / USD 10**, remaining **USD 9.85586795**, 1,218 total attempts. Zero new provider requests. Raw course PDFs/extracts, keys, private data, databases and experiment logs stay out of GitHub. Publication is authorized; no paid host exists. The one-time resumption at 20:55 IST today is a backup subject to availability; first inspect this checkpoint and the active continuation to avoid overlapping work.

---

# Current checkpoint - reference validation and full beta direction

**6 November 2026.** Continue Beta in Main with canonical D: cwd. Latest user directions supersede the earlier deployment deferral: no teacher is available, find another validation source, and prepare a **full beta with saved learner progress** after validation. GitHub publication remains authorized. R3 graph/diagnosis integration remains owned by its contributor.

Start with Docs/product_quality/v3/REFERENCE_VALIDATION.md, STATUS.md and TOOLS_HANDOFF.md. New standalone validation source is **ea438cf4eae6737e942ed732c21e76f970ba58f1**, published to Beta. **1,789 full four-suite tests and 355 focused checker tests pass locally.** GitHub CI [42236144675](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42236144675) is successful on this source: 1,755 portable tests pass, 34 external-corpus cases are deselected and pass locally, two synthetic registry tests and all three smoke gates pass.

The new stdlib-only exact oracle uses published OpenStax definitions and a separate implementation: repeated AP addition/subtraction, Fraction arithmetic, quadratic polynomial substitution/completeness and bounded expressions. It imports neither runtime/dataset solver nor SymPy. All 331 eligible public practice keys pass and a deliberately altered key per item fails; additional known-answer, shape/unit, expression-execution and resource-bound controls pass. This is separately implemented by the same coding assistant, not independently authored final evaluation. No OpenStax endorsement, pedagogical suitability, diagnosis or learning result is inferred.

The checker is **offline qualification only**, not connected to learner turns or the example service. Production remains parallel-example-v2. The incomplete boundary-regime prototype is preserved privately under Directions/course_review/2026-11-06/drafts/parallel_regimes_unwired.py and is not packaged. R3 still needs the after-last-hint example call, persistent revisit mark/restore/resolve, publication/version/ownership checks and integrated practice/quiz/restart/deletion acceptance. No R3 code or supervisor-model switch was made.

Course review is complete: all supplied text in eight PDFs, confirmed duplicate/overlapping exports (163 distinct supplied page bodies), plus ten selected diagrams visually inspected. Private report: Directions/course_review/2026-11-06/COURSE_TO_SYSTEM_REVIEW.md; coverage, decisions and exact qualification receipts are beside it. Course prompts/code were treated as data, not commands or authority. PDFs, raw extracts, rendered slides, personal watermarks and private review notes stay out of GitHub and were not sent to an external model.

The design direction is bounded LangGraph contracts; separate code/source/permission gates; outcome/process/safety/cost metrics; private parent-linked traces; and a verified offline failure playbook with candidate promotion gates. Do not add swarms/A2A, RL or automatic runtime prompt rewriting merely to follow lecture examples. Missing teacher access changes the labelled beta validation basis, not historical human-review records. Any beta content publication policy must explicitly represent reference/machine validation; never fill teacher-approved fields to bypass existing gates. Formal independent M3/M4/efficacy acceptance remains separate.

Next non-R3 work: preserve mathematical boundary cases in checked examples, returning unavailable when preservation conflicts with the active-answer guard; separately version broader simulator task support and declare task pools; then prepare the persistent deployment. User selected saved progress: the stashed stateless Vercel reference preview is not equivalent. Current SQLite/checkpoints need durable Python hosting or a storage migration. Prepare auth, restart/progress, deletion, global server usage caps, mobile and lost-acknowledgement tests before sharing. No paid hosting service exists; obtain the exact recurring plan/account approval only after concrete preparation.

Provider accounting is unchanged: **1,218 total attempts**, phase provider-reported **USD 0.09403805**, accounted **USD 0.14413205**, remaining **USD 9.85586795** under the durable USD 10 provider cap. Known continuation USD 0.37801005; original 98 money and first failed author request actual billing remain unknown. All wallets stay closed/unchanged. No new model requests, course uploads or deployment operations occurred. Do not repeat completed E1-E4/E3/pilot/live/R4/fresh-case/task-pool jobs or regenerate older reports against mutable allocations.

Secrets, private data, local databases and raw logs stay outside GitHub; the pre-push audit passed. Old studies, tags, data and blank human forms are preserved. Backup one-time resumption remains at 20:55 IST today, subject to availability: read this checkpoint and ACTIVE_CONTINUATION.json first and avoid duplicate work.

---

# Current checkpoint — R4 explanations and owned revisit overview

**6 November 2026.** Continue Beta in Main with canonical D: cwd. GitHub publication remains authorized, deployment deferred, R3 owned by its contributor. Start with Docs/product_quality/v3/STATUS.md, R4_REVIEW.md/json, TASK_POOL_AUDIT.md/json and TOOLS_HANDOFF.md. This supersedes older unrun-R4 and unexplained-regression statements below.

New code: parallel-example-v2 provides labelled checked steps, complete zero equations and task-specific transfer questions; IDs include renderer version. All 331 public practice items retain verified nonleaking examples. A repeated 900-input audit yields 892 verified valid examples/eight rejected invalid inputs. Learner/API overview adds owned revisit counts, teacher-only item details, exact totals beyond the 100-detail cap, stale-version filtering and privacy deletion. No new R3 routing/diagnosis or production model changes; R3 integration remains pending.

Validation: 1434 full four-suite tests and all three local CI gates pass. Remote CI 42227085825 on published 96d7829 is green: 1400 portable tests, synthetic index registration and all three smoke gates pass; 34 corpus-dependent cases pass locally. The initial overview test rendered Chat instead of its callable Progress page; the corrected AppTest invokes the production callable after real app/auth setup, and both role views pass. Initial failed test log is preserved. This is functional AppTest evidence, not new manual/mobile browser acceptance.

R4 paired review: same 18 public examples/numbers plus 12 corrupted controls, frozen before and after. Mean AI clarity 2.611 -> 4.389. Reviewer misses four controls before/five after; one unbound quote each, contradictions retained. Code accepts 18/18 originals and rejects 12/12 controls in each round. AI cannot override verification or grant teaching approval. V2 teacher forms remain blank under r4_review_02/teacher_examples_18.json. Source files/protocols/inputs/raw outputs/budgets preserved in r4_review_01 and r4_review_02. No repeated received/uncertain requests.

Baseline diagnosis decline was isolated to task-pool selection on this simulator. Cached audit: 15 changed AP trajectories/arm, nine lost hit sessions; first divergence is practice selection at turn index 1. An evaluation-only C2 ablation restores the prior 131-item scope, leaves core diagnosis/runtime/simulator/config/data/seeds unchanged, and recovers 0.208 recall/0.625 precision/gain 0.167 with all 48 trajectories identical to v2. Full 331-item scope remains 0.083/0.4/0.083 with 18 unchecked attempts. Product still has 331 items. Broader simulator/task support needs R5/R2 review; fresh-message diagnosis remains weak. See baseline_delta_audit_01 and baseline_task_pool_audit_02. Preflight 01 stopped before sessions on LF/CRLF byte comparison; normalized text fix and original error are preserved. No R3 product code was changed for the audit.

Budget: 1218 total historical/current attempts, known continuation USD 0.37801005; original 98 money and first failed author request actual billing unknown. Phase reported USD 0.09403805, accounted USD 0.14413205, remaining USD 9.85586795 under the durable USD 10 cap. New R4 batches use 60 calls/USD 0.02083425, all costs covered, wallets closed. Every original wallet is unchanged; no paid job is active. R4_NEXT_BATCH.json is now completed via the two recorded rounds; never repeat them. Safe verifiers: report_r4_iteration.py --check, report_v3_fresh_cases.py --check, report_v3_baseline.py --check.

Keep secrets/private data/DBs/raw logs out of GitHub. Deferred mobile/Vercel stash 9cf6a27f25999be536d61eea665bc440bb9ab019 stays untouched. Backup resumption is at 20:55 IST today, subject to availability. No new PRs were open; #1/#4/#5/#6 remain merged. Preserve all old studies/reports/tags, original data and blank human reviews.

This batch is published on Beta as runtime 96d7829, with successful remote CI. Raw CI ZIP/receipt, final qualification and the no-repeat next-session docket are under Directions/product_quality/v3.

Next: continue non-R3 boundary-regime and separately versioned simulator/task-support work from NEXT_SESSION_ACTIONS.json; R3 integrates the handed-off services; R5/R2 independently review simulator coverage and evaluation scope; actual teachers/rater/final authors and release acceptance remain required. Do not author competing R3 routing or silently narrow the product to make metrics improve. Formal M3/M4 completion is not claimed.

---

# Current checkpoint — approved PRs merged, R2/R4 services qualified

**6 November 2026.** Continue Beta in D:\Work\IITB\Socratic Tutor Main; all project commands use canonical D:\Work\IITB\Socratic Tutor. The user authorized GitHub publication, deferred deployment, and requested final-product work outside R3 while its contributor continues R3. Start with Docs/product_quality/v3/STATUS.md, RESULTS.md/json, DATA_SUFFICIENCY.md and TOOLS_HANDOFF.md. This section supersedes older local-only, unrun-generator and deployment-priority statements below.

PRs #1/#4/#5/#6 are merged and closed; integration 8240ce3151af76a1ab08ae58ca16ed6d4fd76903 has exactly the combined tree that passed 1069 premerge regressions. Supervisor/specialist proposals retain their documented provisional acceptance limits. No production supervisor switch or real tool-selection acceptance is implied.

New R2/R4 code supplies durable content-bound revisit memory and verified parallel examples across 331 practice items/nine task families. Role/scope, quiz exclusion, atomic audit rollback, restart and privacy tests pass. R3 owns graph integration; the services are not yet connected to learner turns. Local final checks: all 1423 tests pass (1389 portable + 34 corpus-dependent), and all three CI gates pass. The first expanded remote run (42208855204) passed 1389 tests but failed on 34 external-corpus fixtures intentionally absent from GitHub. Corpus-dependent cases are now explicitly marked; both local partitions pass, and remote recovery 42210471805 on 214b7ef is successful: 1389 portable tests plus synthetic registration and all three smoke gates pass; 34 corpus-dependent cases remain local. See Docs/ci_failure.md.

Fresh evidence is complete: 360 AI-authored cases, fixed 120/120/120 scenario partitions, two frozen builds before any inspection, 720 single-turn offline sessions. Before/merged hits 16/120 -> 19/120; false labels 3/240 -> 6/240; zero unexpected mastery/guard/citation integrity failures, 642 citation snapshots. Separate-family blind AI review: 347 label agreements, six disagreements, seven uncertain/unusable. No R3 tuning, human review or final/learning claim. Preserve the original reviewer failure and reuse received raw outputs; only untouched groups were sent in continuation. Safe no-network verifier: scripts/product_quality/report_v3_fresh_cases.py --check.

Durable private inputs: Directions/product_quality/v3/FRESH_CASE_PROTOCOL.json, before_source, merged_source, case_round_02, fresh_case_replay/before and merged, blind_label_review_01/02, blind_label_review_reconciled_01, REPORT_INPUTS_SNAPSHOT.json and batches/*. New phase totals: 1158 historical/current attempts; provider-reported phase USD 0.0732038, accounted USD 0.1232978 (includes unknown failed-request reservation USD 0.050094), remaining accounted ceiling USD 9.8767022. Known continuation USD 0.3571758; original 98 money and failed request actual money unknown. All five original wallets unchanged; new wallets closed, no paid job running. Never reset/reopen/repeat them.

Secrets, private data, databases and raw logs stay out of GitHub. Deferred Vercel/mobile preview is preserved in stash 9cf6a27f25999be536d61eea665bc440bb9ab019; do not deploy or reapply it during unrelated work. No local preview server is running. One-time backup automation resume-socratic-tutor-after-quota-reset is scheduled for 20:55 IST on 6 November 2026; it must inspect current checkpoint/remote state, not repeat completed experiments/merges. It is a backup subject to quota availability, not a guarantee of background execution.

Current merged-source C1/C2 replay is complete: 96 stub sessions plus six matching smokes, 16 cards with seeds 1/2/3 per arm, zero provider calls, paired trajectories identical 48/48. Recall 0.083/precision 0.4/success 4/48/mean synthetic gain 0.083 for each arm; worse than earlier results, cause not isolated. See Docs/product_quality/v3/BASELINE.md/json. Private human_review_packets contains 18 worked-example and 13 blinded disputed/uncertain-label forms, all blank.

The actual remote failure and successful recovery are documented in Docs/ci_failure.md, with raw ZIP/receipt under Directions/git_delivery. A further seeded R4 audit checks 900 synthetic inputs: 892 verified examples pass separate Fraction/polynomial oracles and the active-item guard; eight invalid prefix-ledger inputs are rejected. Initial fixture failure is preserved under r4_math_audit_01; completed audit, source hash and script under r4_math_audit_02. No R3 code or provider calls changed.

Next: continue R4 presentation/method review using the prepared R4_NEXT_BATCH.json (not started, up to 40 requests/USD 0.90 inside the remaining phase; public examples and deliberate controls only), and hand the R2/R4 API contract and measured diagnosis gaps to R3 for integration, actual R2/teacher review and independent final-data/raters/protocol gates. Avoid authoring competing R3 routing or diagnosis code. Existing M3/M4 studies, tags, original sources and blank human packets remain preserved; formal acceptance is still open.

---

# Publishing checkpoint — v3 LangGraph candidate

6 November 2026. The user now explicitly requests **push everything to GitHub** and a mobile-accessible link. This supersedes Keep Beta local for publication; no merge is requested. Push project source and aggregate reports, excluding .env/keys, private/frozen data, local SQLite and raw experiment logs. Current v3 changes pass **1053** four-suite regressions and 236 focused checks. New graph proposal/verification/clarification is opt-in; C1 remains unchanged; AP practice eligibility is 331. See Docs/product_quality/v3/STATUS.md. No new provider requests: total 1097, phase actual USD 0.0107708. The 312-case generator is prepared but not run; publishing/mobile preview takes priority. Preserve all historical ledgers/data/reports and honest review limits.

---

# Current checkpoint — product v2 complete as a local review candidate

**6 November 2026.** Start with **Docs/product_quality/v2/README.md**, **CURRENT_CHECKPOINT.json**, **RESULTS.json** and **DATA_SUFFICIENCY.md**. Final runtime **2af7ecf**, local tag **beta-product-quality-v2-candidate**. Qualified matched live/baseline source is **779e788**; the final revision completes the existing quadratic source explanation and is separately qualified offline. Keep **Beta local**, cwd canonical D:; no push/PR.

Final **817 regressions** and all three exact local CI gates pass. Fixed panel: **10/32 → 32/32 offline**, **20/32 → 32/32 live**, 42 turns/version per mode, all **45 live references** mechanically verified. Final wording revision also passes 32/32 offline. The completed 96-session C1/C2 stub baseline + six matching smokes has 250 verified references; both arms retain recall 0.208/precision 0.625/success 4/48/mean synthetic gain 0.167. No architecture or learning advantage. Functional pass includes routing/directness, not just mathematical correctness.

The candidate gives direct sourced explanations, retains maths during frustration/support requests, recognises whitespace wrapping while preserving numeric layout, classifies correction as information without mastery, and restores/locks owned quiz/interrupted state. Actual API/UI fault tests and assistant browser at 1280/390px pass; no score/model calls in the synthetic unfinished quiz, no horizontal overflow, servers stopped. First stress failures and test-launch fixture errors remain preserved. Assistant reading of the live outputs caught the missing highest-power condition despite a mechanical pass; source 2af7ecf fixes it with two regressions. Live results stay on 779e788; do not repeat paid jobs to make the final revision look live-tested.

Security replay: 80 cases/condition, no errors; guards on 0/18 measured attacks succeeded, off 1/18, **27 unknown each**. No exhaustive safety/poisoned-index claim. Twelve explanations/seven source paraphrases need actual teacher review. Offline/live paired forms each cover the same 32 cases; final 12-source forms and every rating are blank. The public bank has 665 items but only 131 graph-eligible practice items/four task families plus 12 development quiz items; eligibility is not teacher approval.

The user explicitly approved the fixed public/synthetic OpenRouter payload, model and destination after automatic approval review initially rejected the broad budget wording. The comparison completed once: **36 requests/USD 0.0084464**, all provider costs covered, zero errors/refusals/in-flight. Before 23/.0051912, after 13/.0032552. Root receipt and immutable wallet are under Directions/product_quality/v2. **No calls remain scheduled.** Do not reset/reuse wallets or spend leftovers on repeats.

Total usage **1,097 requests**, known continuation **USD 0.2947428**, original 98 money unknown. Phase actual **USD 0.0107708**, allocated caps USD 0.50, unallocated USD 9.50 under the USD 10 ceiling. Four earlier wallets are byte-identical. Source locks/archives preserve before, live candidate and final revision; 30 historical report documents and legacy run_session AST are unchanged. Safe offline verifier: **scripts/product_quality/report_v2.py --check**. Preserve old reports; v1 generator reads the changed allocation and must not regenerate history.

M3/M4 final gates remain: actual R3/R2 architecture/scope review, stronger diagnosis/connected task coverage, teacher/independent-rater review and independent final author, preregistration/freeze, another person's installation and actual remote CI failure evidence. Original 63-item/40-item packets and four lesson decisions are blank. No formal acceptance or human learning claim. No resume automation, temporary server or paid job is running. Earlier pending-transmission sections below are historical and superseded by the explicit approval/completed receipts above.

---

# Current checkpoint — product v2 qualified offline

**6 November 2026.** Continue local **Beta** in Main; cwd is canonical D: workspace. Start with **Docs/product_quality/v2/README.md**, **CURRENT_CHECKPOINT.json**, **RESULTS.json** and **DATA_SUFFICIENCY.md**. Qualified source is clean **779e788**; no push/PR. Full regression: **815 passed**, including 163 new v2 checks. All three exact local CI gates pass. Fixed public panel: **10/32 before → 32/32 after offline**, 42 turns per version and 44 verified references. Current C1/C2: **96 sessions + six matching smokes**, 250 verified references, both recall 0.208/precision 0.625/success 4/48/mean synthetic gain 0.167. No C2 or human-learning advantage.

The candidate adds direct cited concept help, preserves mathematical intent during frustration/support requests, recognises whitespace-wrapped questions/control phrases without changing stored numeric layout, classifies explicit corrections as information, and restores/locks owned quiz/interrupted state. Actual API/UI fault tests and assistant-operated 1280/390px browser checks pass; synthetic quiz leave/refresh caused no scores or model calls. Servers stopped. First stress failures and one test launch with 34 missing-data fixture errors are preserved; the corrected full launch passes all 815.

Security: 80 cases per condition, zero errors; guards on 0/18 measured attacks succeeded, off 1/18, with **27 unknown/unsupported each**. No exhaustive safety, poisoned-index or final-efficacy claim. Twelve concept explanations/seven source paraphrases still need teacher review. New blank packets: 32 paired public journeys and 12 source explanations. The public bank has 665 items but only 131 graph-eligible practice items/four connected tasks, plus 12 development quiz items; eligibility is not real teacher publication.

**No new provider calls.** A one-shot matched live comparison is prepared (200 requests/USD 0.40 within the USD 10 phase), but automatic approval review rejected execution because the budget statement did not specifically authorize transmitting these payloads to OpenRouter. The user has been asked to approve the fixed public/synthetic payload, destination https://openrouter.ai/api/v1 and model openai/gpt-4.1-mini. **Do not run until that reply arrives.** BATCH_APPROVAL.json is pending_transmission_approval and no v2 wallet/live output exists. Do not bypass the rejection. The durable private coordinator is Directions/product_quality/v2/execute_matched_live.py; it checks approval, clean source and qualification before any calls. If permission arrives, update the exact user decision in the receipt and run this prepared comparison once; preserve any failure and never auto-retry.

Total usage stays **1,061 requests / known continuation USD 0.2862964**, original 98 money unknown. Four old wallets are byte-identical. Phase actual USD 0.0023244; allocated caps USD 0.50; unallocated USD 9.50. Old E1–E4/E3/pilot/v1 live jobs are complete and must not repeat. Current source archives and qualification locks are under ignored Directions/product_quality/v2. Safe no-network verification: **scripts/product_quality/report_v2.py --check**. Preserve old reports; v1's generator reads the now-changed phase allocation and should not regenerate that historical report.

M3/M4 final acceptance remains open: actual R3/R2 specialist/scope review, stronger diagnosis coverage, teacher/independent-rater reviews and independent final authorship, preregistration/freeze, independent installation and remote CI evidence. Existing 63-item/40-item packets and four lesson decisions remain blank. Keep Beta local. No resume automation or paid job is running.

---

# Current checkpoint - product candidate and UI qualified locally

**6 November 2026.** The user explicitly chose **Keep Beta local** and authorized up to **USD 10 for the next product-development phase**. Only USD 0.10 was allocated to the first product batch; actual spend is **9 requests / USD 0.0023244**, all costs exposed, no errors/refusals/in-flight requests. No more requests are needed for the completed batch. Phase authorization/allocation and immutable wallet live under ignored `Directions/product_quality/v1/`. Further batches must be separately recorded within the remaining USD 9.90 unallocated cap, chained from 1,061 actual attempts and the current wallet hash. Never reset a ledger or reuse old pilot/E3 leftovers.

Start with **Docs/product_quality/v1/README.md**, **CURRENT_CHECKPOINT.json** and **RESULTS.json**. Core diagnosis changes are local `8716bcf`; the completed live source is `e6796bf`; the learner UI/current baseline source is clean `3fa4075`. All 647 four-suite regressions passed before UI changes; the latest complete Main/UI/API suite passes 548 checks, including all five new learner UI tests. All three local CI gates pass. The eight public offline/live quality cases pass; 14 live turns, nine model calls, four accepted buffered practice generations, nine mechanically verified citation snapshots. No actual human review or independent content was supplied.

The candidate loads 26 provisional catalogue types (previously nine), uses public statement evidence across AP/trigonometry, adds seven exact AP error-adapter families, preserves ambiguous causes, and never confirms a text-only hypothesis from repetition. A model cannot relabel the observed rule or invent its evidence quote. Self-corrections can exit the probe loop without awarding mastery. AP/trig follow-up no longer uses a quadratic factor story. Five numerical AP adapters remain outside the connected approved practice pool; catalogue availability is not diagnosis accuracy.

The learner UI now sends the chosen chapter, pins it per conversation, keeps per-turn reference snapshots, and recovers already saved replies after lost acknowledgements without automatic replay. Assistant-operated browser checks at 1280/390 pixels used an isolated synthetic, stub-only server; there was no horizontal overflow and the servers were stopped. Browser checks preceded a small history-recovery patch covered by real API/AppTest checks. No new UI provider calls. No real teacher approval is inferred from synthetic validation database fixtures.

Fresh stub C1/C2 qualification is complete: **96 baseline sessions + six smokes**, all six corresponding trajectories match. Both arms: recall 0.208, precision 0.625, success proxy 4/48, synthetic mean gain 0.167; zero execution failures/full detected leaks, all 240 citation snapshots mechanically verified. Underlying data is only 16 shared cards with three seed repeats; no live architecture or learning conclusion follows. The old 50% catalogue-availability ceiling belongs to v3 and must not be asserted unchanged for the new catalogue. Diagnostic generalization is still weak and unqualified.

Total provider usage is **1,061 requests**; known continuation money **USD 0.2862964**, excluding the original 98 requests whose money is unknown. The original, E3 and v3-pilot ledgers remain byte-identical. The original six-session v3 pilot used 16 requests / USD 0.0047916; do not duplicate it. The old v2 E1-E4 reports and frozen tags are preserved and belong to their original source. The v3 pilot reporter still reproduces without changing its report.

Next: actual R3/R2 review of the AI-authored candidate and final scope/protocol; specialist architecture/route contract (two deterministic acknowledgements still carry tutor route without calls); better direct-answer relevance in offline fallback and broader paraphrase/learner trials; actual teacher/rater reviews and independent final authorship; final preregistration/freeze/evaluation. R1/R5 are one person and cannot be two independent raters. Original 63-item and new 40-item packets and four lesson decisions remain blank. Semantic citation/security review, another person's clean installation and actual failed remote CI remain open. Beta is local, so no remote CI/PR was started. Full M3/M4 acceptance is not claimed.

Only safe no-network reporters regenerate completed results: scripts/m3/report_v3_pilot.py and scripts/product_quality/report_results.py. Live/baseline runners refuse existing output; do not move/delete wallets or results to bypass them. The previous pre-pilot offline builder now intentionally refuses an existing wallet; preserve its lock instead. No resume automation or paid job remains running.

---

# Current M3/M4 checkpoint - v3 pilot complete; product quality work next

The user resumed work toward M3/M4 after PRs 2/3 merged. Continue on local **Beta** in `D:\Work\IITB\Socratic Tutor Main`; project cwd is canonical `D:\Work\IITB\Socratic Tutor`. Do not push Beta without the separate publishing request. Start at **`Docs/m3/v3/STATUS.md`** and **`TEAM_ACTIONS.md`**.

## Latest update - approved pilot complete; product quality work authorized

The user approved **80 requests / USD 0.05** for the prepared pilot and explicitly answered **Keep Beta local**. All six sessions finished on clean `a9ee2ba`, using **16 requests / USD 0.0047916**, with no errors, refusals or in-flight requests. All 10 tutor-route turns made model calls; all 48 turn traces and 14 citation snapshots were verified. Total usage is **1,052**; known continuation cost is **USD 0.2839720**, excluding the original 98 requests whose money is unknown. Original/E3 wallet hashes remain unchanged; the new pilot wallet hash is `ca964e400d1424eabc96e3a3531b2ed075606b84356cc7630503e24957461a70`. No pilot sessions remain and unused allowance must not drive repeats.

The quality result is weak: both arms have zero diagnosis hits, zero success proxies and mean synthetic quiz change -2/3, with no C2 advantage in three matched pairs. No explicit diagnose-route turn occurred. The pilot accepts paid tutor paths only; it does not establish product quality, specialist architecture or learning. See `Docs/m3/v3/PILOT_RESULTS.md/json`; rerun only the offline reporter `scripts/m3/report_v3_pilot.py` to verify saved evidence. The original `report_v3.py` builds the pre-pilot lock and now intentionally refuses an existing pilot wallet; never remove/reset a wallet to regenerate it.

The user then said “I think if we even reach around 10 dollars it will be fine I think”, “so work accordingly”, and “I want really nice product”. Treat **USD 10 as the ceiling for the next development phase**, spend in smaller durably capped batches, keep Beta local, and prioritize public-catalogue diagnosis/elicitation and useful learner follow-up before more expensive repeats. Preserve the v3 runtime/tag and old studies; new product changes are candidate work requiring fresh validation. Do not fabricate R3/R2 authorship or review; team ownership/review remains explicit. No final-study or human approvals are granted by budget authorization.

The sections below preserve the pre-pilot offline checkpoint and historical prepared plan. Their pending-approval language is superseded by this actual user decision and completed pilot evidence.

## What is now done

- Merged upstream milestone-2 PR2/PR3 into local Beta (integration3e56deb), preserving token caps and old frozen tags. Current runtime candidate is **e79d7d3**; all 554 regression tests passed, plus 21 focused policy checks after clarifying the test fixtures.
- Context-bound copying is implemented as an **opt-in** policy. Legacy behaviour/default remains available and the frozen run_session AST is identical. It removes only owned-format suffix matches and copying without explicit question context; ambiguous disclosures stay unreviewed, and old qualification flags remain conservative. Actual context-linked full matches and registered-practice telling remain possible. ContextVar scopes isolate concurrent sessions and no hidden quiz reference enters app/model input.
- All six three-chapter smokes passed (18 sessions), complete offline E1/E3/E4 tutoring matrix 224 sessions and E2 security160 cases completed with zero execution errors, and all three exact local CI gates passed. All18 smoke trajectories match full runs; C1/C2 match6/6. All536 offline citation snapshots pass hash/chapter/source checks; semantic faithfulness remains unreviewed.
- The cached 224-session audit reproduces every original baseline.161 of 177 copying witnesses came from the exact app format instruction; 16 are unattributed. All86 old post-copy triggers are removed under the candidate in these fixed trajectories. This is not a new live experiment or a human learning estimate.
- Canonical app/spec/policy copies now match the shared checkout (70 files checked); differing preimages are preserved privately. Dataset libraries/private configs were not replaced.

## The important remaining capability gap

Development cards have 17 seeded types / 24 card-type associations. Runtime loads 9 types and can cover only 12/24 associations: an optimistic **50% development micro-recall ceiling** and 9/17 type-macro ceiling; seven cards have no loaded seeded diagnosis. R3/R2 must work from the public catalogue and distinguishing evidence to complete/review adapters or explicitly settle scope. More repeat runs cannot remove this structural limit. Do not use private learner-card states or simulator rules to author diagnosis rules.

Full specialist-agent/question-setter acceptance is still R3 work; shared heuristic controllers and a positive session call count do not prove it. New telemetry records model calls per tutor-route turn for an actual pilot check.

## Prepared next actions - not approved or executed

A **six-session** C1/C2 pilot is prepared:3 existing cards (one per chapter), seed 1,8 turns, fixed gpt-4.1-mini, template voice, no judge. Proposed separate allowance **80 requests / USD 0.05**. Configs: `eval/configs/m3_v3_pilot_c1.toml` and c2. Runner `scripts/m3/run_v3_pilot.py` defaults to preflight; it refuses pending approval and checks the candidate source/data hashes. Receipt `Directions/m3_runs/v3/PILOT_APPROVAL.json` is **pending**, no approver/quote, no pilot wallet exists. Do not run --execute-live until actual approval. No provider ping or voice/judge requests are authorized.

Existing original wallet stays 1,000 attempts; the separate E3 extension has 36 completed attempts / USD0.0132756. Combined 1,036 used; known continuation cost USD0.2791804 excludes prior 98 unknown money. Both wallet hashes are unchanged. The 14 unused E3-specific requests are not transferable to this new pilot. Never reset or bypass a wallet.

A draft PR body is ready at `Directions/m3_runs/v3/BETA_DRAFT_PR.md`; Beta has not been published. The earlier user authorization covered PR2/PR3, not a new Beta push. Publishing can provide remote CI and team review after an actual user request.

## Human/team review package

- R2 decision template: `Directions/m3_runs/v3/human_actions/FINAL_PROTOCOL_DECISIONS.json`, all actual decision/reviewer/budget/seed fields blank.
- Focused copying-context packet: `Directions/m3_runs/v3/review_packets/post-copy-context-v1/`, 30 unique real contexts + 10 explicitly AI-authored controls,40 items, all labels blank. Keep mapping_private.json hidden. Controls are excluded from study metrics and are not independent final data.
- Existing 63-item leak/targets packet: `Directions/m3_runs/v2/live/review_packet_context_v2/`, untouched and blank. Two real independent people must label; R1/R5 are one person.
- Teacher lesson decisions remain blank in the prior human_actions/lesson_review.csv. R3/R2 scope/rule review, independent final-content/new attack authorship, semantic review, rater/judge calibration or explicit limitation, another member's installation and real failed-CI demonstration remain external gates. `TEAM_ACTIONS.md` states exact inputs/proofs by role. No messages have been sent to the team, and no approval is generated.

## Preserved historical evidence

All original v2 paid E1-E4 development runs are complete (224 tutoring sessions, 160 security cases,899 citation snapshots), including 48/48 candidate E3. Their reports remain `Docs/m4/E3_COMPLETE_RESULTS.*`, with original1,000-request report/tag and private archive preserved. They belong to the old behaviour; do not attribute them to this changed candidate. Final preregistration remains draft and formal M3/M4 acceptance is open.

Safe commands: use shared-checkout .venv and SOCRATES_SOURCE_WORKSPACE canonical. `report_v3.py` recomputes saved v3 reporting. `run_v3_pilot.py` is preflight-only without --execute-live and actual approval. `validate_v3.py` refuses existing runs; inspect completed indexes rather than silently repeat. `audit_copy_policy.py` refuses existing rating output; preserve labels and choose a new packet version if ever needed. No resume automation remains.
