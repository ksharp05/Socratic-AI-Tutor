# Socrates beta design — 3 November 2026

Goal: one usable local beta, grounded in the acquired NCERT collection, with natural English teaching and replaceable knowledge sources. The Devpost Socrates reference informs focused conversation, diagnostics, learning maps, recall, plans and saved sessions. We do not infer flawless teaching from corpus size.

## Boundaries

- **Knowledge port**: versioned scope catalogue, search, passage lookup and source provenance. NCERT SQLite and validated passage-JSONL are adapters. Imports create immutable builds; activation applies to new sessions. Existing sessions pin their original dataset version.
- **Dialogue port**: provider-neutral structured generation. Context includes scoped excerpts and six recent exchanges, never private keys or evaluator material. Code validates reply length, citations, question quality and active-problem boundaries. A labelled extractive fallback handles outages and missing evidence.
- **Assessment port**: the existing team maths kernel computes and checks keys independently of the dialogue model. Public practice prompts are eligible; held-out/quiz benchmark files are never ingested. Diagnostic and quiz submissions withhold feedback until completion; no tutoring model calls during assessments.
- **Study service**: deterministic learning-map observations, source-backed flashcards, self-rated review scheduling, five-day plans and session replay. Exploration, checked answers and self-ratings are distinct; none automatically proves mastery.
- **Persistence port**: SQLite transactional repository, request idempotency, per-session serialization and anonymous-browser ownership. API schemas reject unexpected fields. Local anonymous beta is not a school multi-tenant deployment.
- **Delivery**: FastAPI REST endpoints and local static UI. No provider secrets in JavaScript. One launcher. Default localhost binding, bounded live-call budget, explicit live/offline status, source/version health and useful failure states.

## Data lifecycle

Acquire/verify originals -> extract staff text -> admit candidate passages -> validate dataset contract -> create immutable index -> register version -> activate for new sessions -> observe quality. Source text and local state remain ignored under Directions. Registering data requires a local operator CLI, not a learner chat or public upload. Exact quotes and PDF pages bind curated recovery patches; source hashes remain unchanged.

## Beta acceptance

1. New dataset can be imported and activated without editing dialogue/UI code; an old session still retrieves from its pinned version.
2. A learner can select a supported scope, converse naturally, save/replay a session and see actual citations. Clarification, topic correction, repeated confusion, timeouts and missing evidence have tested behavior.
3. Supported Class 10 maths practice, five-item diagnostics and quiz flows run end to end with code-owned grading and no keys in browser/model payloads.
4. Flashcards, review scheduling, learning map, five-day plan, focus timer and progress/history operate on persisted observations.
5. Ownership, idempotency, invalid input, injection-shaped requests, quiz isolation and provider failure are exercised in tests.
6. Development evaluation uses predeclared questions, retains every outcome, reports denominators and component limitations, and produces best/worst question lists plus an actual measured graph. It is separate from independently authored final evaluation.
7. Desktop and narrow-screen UI flows are inspected. No dead navigation or simulated results. Honest unsupported-scope messages replace fabricated capability.

## Measurement contract

Report retrieval source match against developer-selected source anchors, reply contract/citation-ID validity, expected-route behavior, verified-maths correctness, fallback rate and latency. These are separate dimensions. Do not call a composite technical check an accuracy, learning-effect or human teaching-quality score. Keep unsupported/abstained cases in task-completion denominators while showing correct abstention separately. Freeze the final case file before the measured run; mark tuning/development authorship explicitly. Retain prior failed runs rather than selecting only successes.

## Integration strategy

Implement in the canonical D: workspace as `socrates_beta`. Reuse the team app via bounded provider and checked-maths adapters configured by app-root; do not overwrite its capstone graph or contaminate its held-out evaluations. A shared API mount can use the same app factory, rather than maintain a second implementation. No deployment, commit, push or external student messaging is implied by this local-beta goal.
