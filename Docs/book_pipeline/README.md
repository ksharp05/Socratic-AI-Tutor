# NCERT pipeline and Socrates conversation preview

Implemented 3 November 2026 in `D:\Work\IITB\Socratic Tutor`. This is a working local development milestone using the newly acquired books. It is separate from the team application's existing capstone deployment. The source PDFs, frozen datasets, held-out evaluations and Main app code are preserved.

## Run it

Open PowerShell in the project directory:

```powershell
Set-Location -LiteralPath 'D:\Work\IITB\Socratic Tutor'
.\book_pipeline.ps1 serve --live
```

Open <http://127.0.0.1:8766>. Select a class and subject, then start a conversation. The launcher uses the team app's Python environment and existing provider configuration; it never embeds credentials in browser code. Live mode allows six provider calls per server run by default, with a 20-second request timeout and no provider retries. After the budget or on validation failure, replies are labelled as fallback. Set `--max-live-calls 12` for a longer local trial (hard maximum 20). Do not expose this unauthenticated development server beyond localhost.

Without `--live`, the same screen exercises session, retrieval and fallback plumbing; its fixed questions are explicitly an offline scaffold, not evidence of natural-language generation.

```powershell
.\book_pipeline.ps1 search 'photosynthesis' --grade 10 --subject Science
.\book_pipeline.ps1 chat --grade 10 --subject Mathematics --live
.\book_pipeline.ps1 scopes
.\book_pipeline.ps1 build
```

The preview's quiz mode only records messages and returns `Recorded.` It neither serves a question bank nor grades answers. Active maths problems are directed to an unverified first-step discussion without a model call. The shared app retains its existing code-based grading path.

## What is working

The manifest-driven pipeline verifies the top manifest, each volume-manifest hash and each admitted PDF hash. It follows only the two acquired textbook collections; it does not crawl evaluation files. Numbered file indices are kept separate from printed chapter numbers. Common XI/XII books map to both grades, and unusual double-dot filenames are retained.

PDF text is cached with source/extractor hashes and exact PDF-page counts. All decoded pages go to a staff-only SQLite archive. A separate preview index receives English prose candidates after section/task, glyph and layout filters. Detected exercises, worked examples, answers, front/back matter and raw maths are withheld. These filters are imperfect candidate admission, not a guarantee that every unmarked task has been removed. No source receives human approval automatically.

The preview uses a local SQLite FTS5 lexical index, filtered by class and subject, optionally book and unit-file index through the CLI/API. It is not yet hybrid or semantic retrieval. Up to three short passages enter a model request; complete books, private answer keys, evaluator labels and other sessions do not.

The 25 existing normalized Class 10 maths references are imported separately. Every anchor's PDF hash matches the new collection. Their pending human-review status is preserved. They cover Quadratic Equations, Arithmetic Progressions and Introduction to Trigonometry; acquiring all maths books has not supplied checked formula cards or graders for every class.

## How Socrates communicates

The language model handles informal everyday English, explanations and contextual follow-up. We are using a pretrained model, not training an English-language model on the textbooks. Grounded content, dialogue behaviour and mathematical verification remain separate responsibilities.

Each session fixes the class, subject and mode. The tutor retains six recent exchanges and the current topic. A reply such as “I don't know” keeps that topic. “Actually, I meant respiration” changes it. Repeated confusion selects a smaller step, then an analogy, then a prerequisite question; an explicit request for an analogy is honoured immediately.

A generated reply should acknowledge the learner's thought, explain one useful idea and end with one focused question, within 60 words. Follow-up questions should reveal reasoning, rather than ask whether the explanation merely feels clear. Citation IDs must come from the retrieved excerpts. Unknown citations, repeated questions, unverified grading phrases, multiple questions, overlong replies and generic understanding-check questions trigger a labelled fallback.

Examples from the revised real-provider development trial:

- Learner: “I know plants need sunlight, but how does photosynthesis turn it into food?” Socrates explained the input materials and asked which two substances the plant takes in.
- Learner: “I'm still confused. Could you explain it with an everyday analogy?” Socrates retained photosynthesis and offered a solar-powered-kitchen analogy, then asked about chlorophyll's role.
- Learner: “Explain what quadratic means in simple English…” Socrates used the idea of squaring and asked for a simple example.

These are observed development outputs, not reviewed model answers. Analogy fidelity and precision of maths wording still require assessment; the presence of a valid citation does not establish semantic entailment. No model response awards correctness, marks or mastery. The concept preview reports `verification: not_assessed`.

Basic email/phone redaction occurs before persistence and generation. Session IDs are random; history is isolated and capped. The UI can delete a conversation. Sessions older than 30 days are removed on the next preview start. This is limited local data minimisation, not a complete privacy system. Distress language routes to a brief request for immediate human support without claiming that any notification was sent.

## Reference decisions

The [Socrates Devpost project](https://devpost.com/software/socrates-ai-powered-socratic-tutor) inspired focused Socratic questions, diagnostic conversation and remembered sessions. Its reported feature list is an author's description, not effectiveness evidence. We did not copy its code. We have deferred voice, knowledge-map UI, flashcards and teacher dashboards, and have retained the capstone boundary against revealing an active problem's answer after repeated struggle.

## Actual build and validation

| Measure | Result |
|---|---:|
| Source volumes represented in manifest | 145 |
| Usable PDF assets extracted | 1,605 / 1,605 |
| PDF pages extracted, page counts checked | 25,175 / 25,175 |
| English prose candidates in preview | 10,851 |
| Normalized maths references | 25 |
| Books with at least one preview passage/reference | 86 |
| Class/subject combinations in preview | 53 |
| Human approvals / production admission | 0 |
| Behavioral contract tests | 27 passed |
| Revised real-model replies accepted by structural guards | 3 / 3 |
| Revised quiz / access-claim / active-problem model calls | 0 |

The first live trial made six calls. Its generic “does that make sense?” questions and an imprecise analogy motivated a prompt/guard revision. All six outputs are retained. The revised probe made three further calls, for nine total development calls; failures were not silently retried. Tokens and latency are recorded where supplied; monetary cost is unknown. These trials do not measure learning gains, factual accuracy, attack resistance or independent final performance.

Six cross-grade retrieval smoke queries produced hits for five and no result for Class 8 Science friction. The source text exists, but conservative section/layout admission has withheld it. Hits alone do not establish relevance: there are no gold relevance judgments or recall scores for this new corpus. Grade 11 motion queries can also retrieve later applications without a chapter filter. Better chapter/concept metadata and ranking are next work.

The localhost UI was opened and exercised through the browser, including sending an offline question. HTTP checks confirmed page loading, a concept turn, quiz recording, session deletion, and rejection of foreign Host/Origin requests. The temporary test server was stopped after verification.

## Source quality and coverage limits

Two extractor UTF-8 errors were recovered transparently: `hhml106.pdf` and `hekb106.pdf`. Exact extractor stdout bytes and hashes are retained alongside replacement-decoded text. Pages containing replacement characters cannot enter the prose preview. This is not a repaired publisher PDF or an OCR result.

The machine-generated page queue includes 7,686 pages awaiting non-English processing, 1,995 maths pages awaiting normalization, 249 English sparse/possible-scan pages, 74 English glyph-damage pages and 10 other English-language quality exceptions. “Sparse” does not prove a scan; some pages are intentionally almost empty. The overall raw page-quality counts also include non-English books and should not be mistaken for English OCR counts.

Existing acquisition gaps remain: Class 9 ICT is Coming Soon; official Class 11 Urdu `kuga104.pdf` is malformed and excluded before extraction; Class 12 Urdu catalogue/edition coverage is unresolved. Hindi/Sanskrit/Urdu and Hindi music originals are retained in the staff archive but are not taught by this English-first preview. Seven maths volumes have no normalized preview references yet. Images, diagrams, table geometry and formula fidelity are not recovered by this text pipeline.

## Files and ownership boundary

- `src/ncert_pipeline/`: catalogue validation, extraction, admission, retrieval, provider adapter, dialogue, CLI and web preview.
- `tests_book_pipeline/`: development-authored contract fixtures, not independent held-out cases.
- `scripts/book_pipeline/probe_live.py`: explicit three-call live probe; invokes the configured provider and can incur a charge.
- `Directions/book_pipeline/v0_1/BUILD_REPORT.json`: source pins, extraction counts, exceptions, output hashes and coverage.
- `Directions/book_pipeline/v0_1/staff_pages.sqlite` and `text_cache/`: private full extracted text; never serve these through the learner API.
- `Directions/book_pipeline/v0_1/preview.sqlite`: pending-review, concept-only candidate index with 25 normalized maths references.
- `Directions/book_pipeline/v0_1/SOURCE_QUALITY_QUEUE.jsonl`: machine-proposed remediation queue.
- `Directions/book_pipeline/v0_1/RETRIEVAL_SMOKE.json`, `HTTP_SMOKE.json`, `LIVE_CONVERSATION_PROBE*.json`: actual development evidence.
- `Docs/book_pipeline/VALIDATION.json`: compact validation receipt and code hashes.

All source text, indices, sessions and probe transcripts remain under the already Git-ignored `Directions/`. No sources, keys or benchmark material have been published. The new package is additive in this workspace and is not enabled in `D:\Work\IITB\Socratic Tutor Main`.

## Next implementation milestones

1. Recover high-value withheld English topics starting with Class 8 friction. Add reliable heading/layout metadata and validate exercise/answer separation against a sampled review set. Use page-rendered/OCR fallback only where needed; retain original page anchors and uncertainty.
2. Create concept/chapter mappings and verified maths-reference cards for additional grades. Attach symbolic/numeric checkers and domains to each supported problem family before accepting an answer as verified. Use books for facts and code for calculable claims; reserve human review for content interpretation and teaching quality rather than hand-calculating every numeric variant.
3. Measure scoped retrieval on a development set with explicit supporting passages, then compare dense/hybrid retrieval and reranking against this lexical baseline. Keep independently authored final evaluation out of tuning.
4. Connect this pipeline to the Main app through a reviewed adapter: preserve code-owned grading, quiz isolation, admission policy and private evaluator separation. Start with the existing three Class 10 chapters plus a small source-grounded science pilot, rather than silently claiming full 8–12 teaching coverage.
5. Run labelled multi-turn learner trials for natural English, misconception handling, useful follow-up questions, grounding, analogy precision and graceful recovery. Add teacher handoff, durable progress and diagnostic onboarding only when the actual integration supports them. Voice can follow the text conversation; it is not needed to validate this milestone.
