# Socrates beta: use, extend and test

Implemented in `<project-checkout>`, 3 November 2026. This is a local, anonymous-browser beta with actual textbook retrieval, a configured language model and code-checked Class 10 maths practice. It is ready for supervised beta trials, not certified flawless teaching or public school deployment.

## Start

```powershell
Set-Location -LiteralPath '<project-checkout>'
.\socrates.ps1 serve --live
```

Open http://127.0.0.1:8770. If the handed-off server is already running, open that URL directly. Stop it with Ctrl+C in its console before starting another copy. Omit `--live` for explicitly labelled source-reading recovery without a model. The old `book_pipeline.ps1` preview is retained; `socrates.ps1` is the integrated beta launcher.

The launcher checks `SOCRATES_PYTHON`, then `.venv_beta`, then the configured team app's environment. `config/beta/local.json` controls app-root, data directory, port and live-call budget. Its app-root points to the existing team source adapters, not an embedded credential. Runtime versions are pinned in `requirements-beta.txt`; test/chart additions are in `requirements-beta-dev.txt`. A fresh environment can install those requirements, but must also have the configured team source checkout. No fine-tuning is required to converse in English.

Provider credentials stay in the existing server environment/team configuration. Default budget is 60 provider calls per server run (maximum 120), with 22-second timeout, no transport retries, and at most one separately counted repair for a benign reply-format failure. Unknown citations, grading claims and unsafe practical suggestions trigger source recovery rather than an unrestricted retry. Budget exhaustion is visibly labelled as source-reading mode.

## Connected user journey

1. Set class, subject, study time and goal. Choose a real textbook topic, then ask in everyday English.
2. Socrates responds briefly, asks a focused question and attaches inspectable source citations. Six recent exchanges supply conversational context; complete sessions can be replayed. Topic corrections, typos, simpler wording and analogy requests are supported.
3. For Class 10 maths, start guided practice, a five-item branching diagnostic or a five-item self-check. Submitted mathematical answers are checked by the existing kernel; free-text reasoning is not scored. Hints are staged. Diagnostic/quiz feedback is withheld until completion, and tutoring is paused across this browser profile while a check is active.
4. Save a cited passage as a source card, reveal it and choose Again/Hard/Good/Easy. Ratings schedule the next review; they do not establish mastery. The learning map, observed-answer dashboard and five-day plan use persisted activity.
5. Use the 25/5 focus timer, return to saved conversations, or inspect the beta's recorded question results. All navigation leads to implemented services.

The reference is [Socrates on Devpost](https://devpost.com/software/socrates-ai-powered-socratic-tutor). This implementation uses its focused-question, diagnostic, recall, planning and session-history ideas; it does not copy its code or claim its results. The learning map uses available reading/concept records and explicit prerequisite metadata rather than inventing a universal knowledge graph.

## Modularity and adding data

`ports.py` defines knowledge and language contracts. `knowledge.py` implements scoped search and an immutable dataset registry. `language.py` is the replaceable provider adapter. `maths.py` wraps the team kernel. `repository.py` stores local state, `study.py` implements study features, `dialogue.py` owns tutoring policy, and `api.py` composes the services. The browser has no provider credentials or answer keys.

A dataset version is a read-only knowledge index with hash-bound registry metadata. Sessions pin a version; activation affects the default for new sessions. The registry is re-read by the running application, and Data library refreshes its catalogue. Import/activate through a local operator CLI; a learner message cannot register data. Use one import operator at a time.

```powershell
# Inspect existing immutable versions.
.\socrates.ps1 datasets

# Add prepared exact-source passages to an existing version, creating a new version.
.\socrates.ps1 import --file 'Directions\my-new-passages.jsonl' `
  --id 'ncert-extension-001' --title 'NCERT plus new readings' `
  --base 'ncert-2026-11-03-beta3' --activate

# Activate a previously registered version, or register a compatible prepared index.
.\socrates.ps1 activate ncert-2026-11-03-beta3
.\socrates.ps1 register-index --file 'Directions\prepared\knowledge.sqlite' `
  --id 'prepared-collection-001' --title 'Prepared collection' --activate
```

The JSONL adapter requires `id`, `grades`, `subject`, `book`, `title`, `text`, `page`, `source_file`, `source_sha256`, and an HTTP(S) `source_url`; `source_id` and `unit_file_index` are optional. Quote text must exactly match the whitespace-normalized specified original page. Source hashes are checked; PDF pages use the explicit pdftotext executable, and text originals use page 1. Duplicate IDs, changed hashes, unsupported grades, non-source quotes and dangerous URL schemes are refused. All imported content remains review-pending. Raw mathematical quote import is intentionally refused: normalized references and a compatible checker must arrive through a maths adapter.

Working examples are in `Directions/beta_data/imports/`. The primary-reader recovery was actually added with this CLI, on top of beta2, without changing dialogue or browser code. Existing beta1/beta2 sessions retain their versions. `scripts/beta/prepare_reader_patch.py` reconstructs that import from the verified staff source archive. To recreate the release after `socrates.ps1 init`, run that script and the documented import with its JSONL file. New versions may not overwrite an existing version ID.

## Coverage

The active beta3 index has 10,878 passages: 10,853 prose candidates and 25 normalized maths references, across 86 books and 53 class/subject combinations. It derives from all 1,605 usable source PDFs / 25,175 extracted pages; acquiring/extracting a source is separate from admitting it for teaching. Exact-source additions recover Class 8 friction and the primary Class 10 reader's Lencho introduction.

The public practice adapter contains 665 items across 17 task families, spanning Quadratic Equations (160), Arithmetic Progressions (320) and Introduction to Trigonometry (185). It accepts scalar, finite-set, Boolean, classification, coefficient and defined/undefined answer shapes. Independent arithmetic checks in the development run cover six selected examples; the per-family parser tests are contract tests, not independent mathematical evaluation of all 665 items.

| Capability | Current boundary |
|---|---|
| English concept conversation | Admitted English sources in available class/subject scopes |
| Checked practice/diagnostics/self-check | Existing three Class 10 maths chapters |
| Maths for other grades | Source holdings exist, but normalized teaching/checking adapters are not yet admitted |
| Hindi/Sanskrit/Urdu teaching | Originals retained; non-English retrieval/teaching not enabled |
| Images, diagrams, audio/voice | Not implemented in this text beta |
| Current facts / live data | No live market, weather or news tools |
| Teacher workflows | Existing protected Main API retained; anonymous beta progress is separate, with no new school-wide teacher dashboard |
| Learning or mastery claims | Not measured; shown activity and answer checks only |

Unresolved publisher defects, raw formula/table/diagram extraction and source-semantic review remain in the acquisition/pipeline records. The prototype's text filters and source-ID checks do not prove that every passage is appropriate or every model claim follows from it. Generated analogies, numeric examples and follow-up difficulty need independent review. This is why the beta question list includes limits rather than presenting a flawless-corpus claim.

## Shared application integration

The Main API now has an optional mount implemented in `src/tutor_api/beta.py`. Enable it by setting `TUTOR_BETA_CONFIG` to this workspace's `config/beta/local.json` before creating the Main API; optionally set `TUTOR_BETA_LIVE=1`. The same beta app appears at `/beta/`. The original bearer-token student/teacher routes remain unchanged and their existing 13 API tests pass. The mount is explicitly local, retains the beta's anonymous-browser boundary and is not a public deployment configuration.

Mounted beta practice, quizzes and diagnostics use only current teacher-published question sets and cancel a check if its approval changes. The standalone beta remains a development preview without teacher publication checks. The mounted beta uses the running API checkout for its maths adapter; anonymous beta state remains separate from authenticated graph learner state. See [the mounted approval workflow](../m2/MOUNTED_BETA_APPROVAL.md).

Quiz observations are withheld until the check is complete, and other-session practice, source cards and development results are paused during a check. The beta plan reports a reason based on completed checked answers. Recognized urgent messages receive immediate guidance but are not saved or sent to a teacher. These mechanisms and their limits are described in [beta quiz integrity](../m2/BETA_QUIZ_INTEGRITY.md).

The beta uses a signed, HttpOnly, SameSite browser cookie for ownership. It checks session/card ownership, Origin/Host, closed request schemas and idempotency IDs. SQLite state is private under `Directions/beta_data/`; normal chat keeps no raw provider audit. The local evaluation harness can explicitly audit model output into its ignored run folder. Browser cookies last 30 days; server history remains locally until cleared. No external teacher notifications are sent. No real learner study was conducted; browser acceptance used an assistant-operated anonymous test profile.

## Validation and reproduction

```powershell
$env:PYTHONPATH = '<project-checkout>\src'
& '.\.venv\Scripts\python.exe' -m pytest `
  tests_beta tests_book_pipeline -q --basetemp Directions\beta_data\pytest_tmp

# This makes real provider calls and records every outcome in a fresh private run directory.
& '.\.venv\Scripts\python.exe' scripts\beta\evaluate.py
& '.\.venv\Scripts\python.exe' scripts\beta\render_results.py
```

The cases are `Docs/beta/DEVELOPMENT_CASES.json`; their bytes are frozen into every run. Each run pins dataset hash and runtime source hashes. All runs and any raw development audits stay under `Directions/beta_data/evaluation_runs/`. Results used during fixes are development evidence, not an independent final test. No held-out evaluation files were read. Format repairs consume actual additional model calls and are reported.

See `EVALUATION_RESULTS.json` for recorded results, `QUESTIONS_TO_TRY.md` for the strongest/weakest questions and interpretation, and `performance.png` / `performance.svg` for the graph. `question_results.csv` is the tabular export. The graph measures declared technical task completion and latency, not factual accuracy, teaching quality or learning gains. The chemistry description guard's false-positive diagnosis is preserved in the run history.

## Beta testing next

Use the supplied questions to check reproducibility, then collect a fresh, separately authored sample of learner questions. Include ambiguity, misconceptions, informal English, unsupported material and interrupted sessions. Have reviewers assess factual support, pedagogical usefulness, source precision, appropriateness of examples and false blocks. Record problems before tuning on them. Broader subject/grade checkers, source admission quality and any multi-user/public deployment remain separate work; dataset size alone does not close those gates.

## Shared-checkout setup

`Directions/` is intentionally ignored and must be acquired locally. Copy `config/beta/local.example.json` to `config/beta/local.json`, set `app_root` to the team checkout if needed, and set `SOCRATES_SOURCE_WORKSPACE` to the directory containing the acquired `Directions/` collections. The default assumes that directory is the checkout itself. Set it to the folder containing your local source collection if that folder differs from the checkout. No credentials or textbook PDFs are included in Git.
