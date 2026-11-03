# Book-grounded knowledge acquisition plan

Prepared 3 November 2026. Scope: English-language Class 10 Mathematics — Quadratic Equations, Arithmetic Progressions and Introduction to Trigonometry. Working directory: `D:\Work\IITB\Socratic Tutor`.

## 1. Outcome and definition of enough

Build a small, complete knowledge base from official sources, with traceable mathematical claims, executable checks and retrieval that works with ordinary student English. Use the existing language model for general English; the project does not need to collect a general English pretraining corpus or fine-tune a model to begin.

Mathematical truth will come from authoritative books plus deterministic checks. Human effort should concentrate on ambiguous extraction, curriculum exceptions, teaching decisions and the capstone's explicit human-review/calibration requirements. A mathematically checked item is not automatically a helpful hint or a human-approved item.

The first usable candidate is enough when:

- Every selected learning outcome has source support and an explicit scope decision, starting with the existing 25 concepts. Add missing concepts when coverage requires it; 25 is not a ceiling.
- All admitted formulas, tables and supported problem types have recorded assumptions and passing checks. Unsupported or uncertain claims remain unresolved, not implicitly verified.
- Every tutor-visible factual card has a stable source citation; worked answers and grading keys remain outside tutor retrieval.
- Development retrieval and conversational checks meet the declared gates in section 8, with failures retained.
- A reproducible versioned export and source ledger can be reviewed and loaded by the application under its admission policy.

There is no minimum number of book pages, tokens or generated variants that proves readiness. This is a knowledge/RAG acquisition plan, not a claim of production approval or learning effectiveness.

## 2. What we already have

A read-only check on 3 November confirmed that all nine retained PDFs match their recorded SHA-256 hashes. Their manifest records 121 pages. This check did not reparse page counts or compare current remote bytes. See `source_inventory_audit.json`.

| Existing asset | Evidence and intended reuse |
|---|---|
| Three NCERT textbook chapters | 55 recorded pages: Quadratics 11, AP 24, Trigonometry 20; manifest records Reprint 2026–27. Primary teaching sources. |
| Three NCERT exemplar units | 38 recorded pages: 9, 15 and 14. Supplemental reasoning/problem coverage, filtered by current scope. |
| CBSE syllabus, sample paper and marking scheme | 28 recorded pages: 10, 6 and 12. Scope and assessment references; marking scheme remains verifier-only. |
| Extracted pages and 176 coarse review chunks | Existing acquisition README reports these; audit the extraction rather than treat every chunk as retrieval-ready. |
| 25 concept references and source evidence | Reuse the newer v0.10.0 references and versioned page evidence after checking source/edition bindings. Older v0.1 notes are not the current serving authority. |
| Existing mathematical and dialogue candidates | Reuse eligible practice records and the repaired v0.2 message derivative. Preserve all frozen builds, private benchmarks and review statuses. |

The expanded v0.2 package is development data, not an authoritative book. Its 928 dialogues and 2,400 messages can help test the pipeline; they cannot establish textbook facts or independent evaluation results.

## 3. Source priority and acquisition decisions

| Priority | Source | What to acquire or reuse | Rule |
|---|---|---|---|
| P0 | [CBSE curriculum 2026–27](https://cbseacademic.nic.in/curriculum_2027.html) and [Class X Maths syllabus](https://cbseacademic.nic.in/web_material/CurriculumMain27/SecPart1/Maths_SecP1X_2026-27.pdf) | Scope statements and relevant learning outcomes | Curriculum decides inclusion; record the chosen academic year. |
| P0 | NCERT textbook: [Quadratics](https://ncert.nic.in/textbook/pdf/jemh104.pdf), [AP](https://ncert.nic.in/textbook/pdf/jemh105.pdf), [Trigonometry](https://ncert.nic.in/textbook/pdf/jemh108.pdf) | Definitions, conditions, formulas, derivations, relevant diagrams and conceptual explanations | Use official files and exact edition/hash; preserve originals. |
| P1 | NCERT exemplar: [Unit 4](https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep204.pdf), [Unit 5](https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep205.pdf), [Unit 8](https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep208.pdf) | Alternative reasoning, counterexamples and question structures | Older or combined-topic material must pass the scope map before admission. |
| P1 | [CBSE sample paper](https://cbseacademic.nic.in/web_material/SQP/ClassX_2026_27/MathsStandard-SQP.pdf) and [marking scheme](https://cbseacademic.nic.in/web_material/SQP/ClassX_2026_27/MathsStandard-MS.pdf) | Question styles and verifier/rubric references | These are public development references, not unseen evaluation. |
| P2 | Other books or tutoring datasets | Only a documented gap left by P0/P1 | Do not bulk-acquire more books or generic English text for the first release. |

The official NCERT textbook/exemplar pages were accessible in the research tool on 3 November. The viewed textbook chapters display Reprint 2026–27. CBSE requests returned HTTP 502 during this planning pass; retain the already-hashed local copies and mark remote freshness pending. A failed web request does not invalidate the retained copy or justify claiming it is freshly downloaded.

The exemplar trigonometry unit also covers applications, so its whole unit must not be automatically admitted to our narrower chapter scope. Keep the existing T08 complementary-angle quarantine until its exact current-edition/syllabus mapping is resolved. Do not infer inclusion from an older book or matching ID suffix.

For each acquisition: record official URL, redirects, retrieval time, edition/reprint, file hash, bytes, page count, content type and existing source-use status. On a changed remote hash, retain a new version and produce a diff; never overwrite a retained source or silently update citations. Respect the project's existing private-source/no-PDF-redistribution boundary. Source-use metadata is not permission to package book text or indexes publicly.

## 4. Acquisition and processing pipeline

| Step | Owner role | Work and output | Exit condition |
|---|---|---|---|
| K01 — pin sources | R6 with R2 | Reuse verified PDFs; complete `source_registry.json` and download only missing/changed official versions | All required files present, hashes/editions recorded, changes explained |
| K02 — map scope | R2 | Create `curriculum_map.jsonl`: learning outcome → concept → textbook section; classify exemplar sections and exceptions | Every outcome marked included, excluded or unresolved; no unresolved item in serving export |
| K03 — extract | R6 | Native PDF extraction first; retain page coordinates, tables, diagrams and extraction method; OCR only failing regions | No lost page ranges; reading order and formula/table flags recorded |
| K04 — normalize claims | R2 + R6 | Create atomic `claims.jsonl` and `concepts.jsonl`; preserve exact evidence separately from original explanations | Every admitted factual claim links to a source span; new derivations explicitly labelled |
| K05 — calculate | R2/tools owner | Run deterministic formula, identity, domain, table and answer checks; create `verification.jsonl` | Every checkable admitted claim passes; unsupported forms explicitly withheld |
| K06 — prepare retrieval | R3 + R6 | Build safe passages, concept/prerequisite links and a versioned lexical/vector index | Only permitted factual material enters the index; no keys/solutions/private labels |
| K07 — English/context probes | R1 + R3 | Map informal language to concepts; select balanced contextual dev messages and create retrieval probes | Tested context use, clarification and abstention; synthetic expectations clearly labelled |
| K08 — package and inspect | R3/R4 + R6 | Produce pinned candidate export, inventory, coverage/failure report and loading smoke test | Gates in section 8 met; current human/example promotion policy remains intact |

Roles identify responsibility; no particular person is assigned or contacted by this plan. Independent evaluation remains R5-owned.

### Extraction and source faithfulness

Keep fractions, radicals, superscripts, subscripts, inequality signs, units, angle symbols and diagram labels attached to their source regions. Never repair a formula solely because an LLM says it looks right. Compare independent extraction representations where possible; quarantine conflicting fractions/tables for source-image inspection. Record assistant visual checks as assistant checks, not human review.

A symbolic equality check proves a mathematical relationship under its assumptions; it does not prove that OCR faithfully transcribed the book. Check source fidelity and mathematics separately. A book's conditions, exceptions and figure/reference-angle assumptions are part of the claim.

Split passages at a definition, explanation or derivation boundary. Start around 150–400 tokens when useful, but retain a complete mathematical unit and linked context even when longer. Chunk count is an output of coverage; it is not a quota. Do not copy the existing 176 coarse chunks directly into a serving index.

### Mathematical verification

| Chapter | Required executable checks |
|---|---|
| Quadratics | Nonzero leading coefficient; standard form after simplification; exact roots and substitution; both branches; repeated/no-real-root cases; admissible roots in word problems. Compare solving and substitution/coefficient relationships where applicable. |
| AP | Indexing from the first term; signed/zero difference; positive integer term counts; term membership; formula versus enumerated finite sums; inferred parameters checked against original constraints. |
| Trigonometry | Reference angle and side roles; exact radicals/fractions; degree conventions; ratio denominators; defined/undefined endpoints; all 30 standard-angle table cells; identities checked symbolically with domains, not only numerical samples. |

Use bounded safe parsing, exact arithmetic where supported, rejection tests and checker version hashes. Shared library dependencies must be disclosed; two routes using the same dependency are not independent software implementations. Invalid, failed and unverified are distinct outcomes. An unverifiable student explanation is not automatically incorrect.

## 5. Structured knowledge and access boundaries

Each source-backed claim needs at least:

`claim_id`, `concept_id`, `claim_type`, `statement`, `normalized_math`, `assumptions`, `source_id`, `source_sha256`, `edition`, `section`, `pdf_page_1based`, `printed_page`, `span_or_bbox`, `origin`, `source_support_status`, `text_fidelity_status`, `math_check_status`, `checker_version`, `scope_status`, `permitted_use`, `content_sha256`.

Keep source support (`exact_span`, `derived_from_span`, `unresolved`), mathematics (`passed`, `failed`, `unverified`, `not_applicable`) and human review (`not_reviewed`, actual decision) as separate dimensions. Original paraphrases and new derivations keep source links without being represented as quotations.

Build three distinct views:

1. **Tutor knowledge:** eligible definitions, prerequisites, identities, conditions, conceptual explanations and safe diagram metadata, with citations. Use original summaries when appropriate and preserve their support records.
2. **Verifier-only:** exercise-specific worked solutions, answer appendices, sample marking schemes, generated keys and detailed grading contracts. Formula knowledge is still allowed; disclosure of the active problem's answer requires separate output controls.
3. **Evaluator-only:** independent cases, gold labels, attacks and hidden learner cards. Do not read or merge the existing private held-out case text while implementing this plan.

Selective extraction must separate a definition from a worked answer on the same page. A chapter-wide allowlist alone is insufficient. Use explicit export allowlists, trusted configuration and an application/container boundary; Git ignore rules are not runtime permissions.

The new factual-knowledge admission gate is separate from `v02_integration.promotion`, which currently handles reviewed dialogue examples. This plan does not relabel pending content as approved, weaken that workflow or enable the shared application. Any new source-backed serving policy must be explicit and versioned; it need not require a human to recalculate every mechanically verifiable record.

## 6. English communication and teaching knowledge

Books supply mathematical language and explanations. The existing language model supplies general English. The project-specific data should teach/test the connection between informal messages, prior context and the correct mathematical next action.

- Start with the existing 90 glossary drafts; reconcile them to textbook terms and record unsupported definitions. Add practical aliases such as "common gap" for common difference, while marking aliases as team-authored rather than textbook quotations.
- Select **200 existing contextual development messages**, 10 per intent, from the repaired message derivative. Include spelling errors, missing notation, corrections and references to earlier turns. Keep paraphrase families visible; 200 is a proposed engineering subset, not 200 independent observations.
- Prepare **75 development retrieval probes**, three per starting concept: direct wording, informal wording and a conditions/misconception question. Add **25 negative or underspecified probes** for clarification/abstention. Add probes when the concept inventory expands. These are proposed local targets, not capstone requirements.
- Use the prepared 116-dialogue review queue to inspect scaffolding, repeated failed hints and learner recovery. Keep the full 2,400-message pool and two blind 480-task views available for later annotation; do not duplicate them to claim new data.
- Produce new conversations only for demonstrated failures. The existing 60 adult teacher-led conversations/300 independently authored messages remain a later collection proposal in the expanded-data acquisition plan, not a prerequisite to extract textbook knowledge.

Synthetic expected labels support regression testing. They do not establish real-user intent accuracy, teaching effectiveness or independently measured NLP performance. No new English corpus download or model fine-tuning is necessary for this acquisition phase.

## 7. Deliverables and storage

Create new material under the already Git-ignored area `Directions/_knowledge_acquisition/2026-11-03/`. Reuse original source files by reference; do not edit frozen builds or the original v0.2 package.

| Proposed output | Purpose |
|---|---|
| `source_registry.json`, `curriculum_map.jsonl` | Versioned provenance, edition and scope |
| `extraction/pages.jsonl`, `extraction/regions.jsonl` | Private source text, coordinates and diagram/table relations |
| `knowledge/claims.jsonl`, `concepts.jsonl`, `glossary.jsonl` | Structured facts and the concept/prerequisite map |
| `verification/claim_checks.jsonl`, `failures.jsonl` | Reproducible calculation/source-fidelity evidence and unresolved exceptions |
| `retrieval/passages.jsonl`, `index_manifest.json` | Selective candidate retrieval corpus, hashes and configuration |
| `dev/retrieval_probes.jsonl`, `conversation_probes.jsonl` | Development-only engineering cases; no independent gold claim |
| `exports/knowledge_v0001/` | Minimal pinned factual candidate projection; no solutions or private review data |
| `reports/coverage.json`, `acquisition_report.md` | Exact counts, unsupported gaps, source changes and gate results |

Keep this plan, source hashes, schemas/code and text-free aggregate reports under `Docs/knowledge_acquisition/` or appropriate code folders. Future commands and schemas are implementation deliverables; this planning task does not pretend they already exist. Prefer a lexical baseline before adding vector retrieval so any benefit is measured.

## 8. Acceptance and stopping rules

| Gate | Evidence needed |
|---|---|
| Source integrity | Every source and admitted claim has a verified hash and stable page/section/span reference; remote freshness and permissions are separate fields. |
| Curriculum coverage | All selected outcomes mapped; unresolved scope, unsupported diagrams and T08 remain outside export. |
| Mathematical validity | All supported admitted formulas/answers pass domain-aware checks; corrupted signs, fractions and denominators are rejected by meaningful tests. No solver success is substituted for source-fidelity evidence. |
| Retrieval | Proposed development Recall@5 target ≥0.90 on source-linked positive probes, with per-chapter counts, support sets and misses retained. Report label provenance; matching a citation ID alone is not semantic support. |
| English/context | Each of 20 intents represented in the engineering subset; track correct routing, ambiguity handling and context retention. Do not report human-gold F1 from synthetic labels. |
| Isolation and output | No verifier/evaluator records in exported index; active-answer leak, quiz, role and malicious-source checks exercised. Passing a suite does not prove universal semantic safety. |
| Reproducibility | Same pinned inputs/config produce identical corpus/export hashes; a source revision produces an explicit new version. |
| Honest approval status | Separate source-backed, machine-verified and human-reviewed labels. Human-reviewed Reflexion lessons, question publication controls and 20+ human-labelled judge-calibration outputs remain required by the recorded capstone requirements. |

Once coverage and these candidate gates pass, integrate and evaluate the knowledge base instead of generating more numeric variants. Add material only for an observed coverage, retrieval, reasoning or communication failure. Stop/withhold affected records on source conflicts, unsafe extraction or unsupported checker forms; continue unaffected chapters.

## 9. Proposed schedule before submission

These are planned windows from 3 November, not completed milestones. Engineering steps may overlap across the six team roles; unresolved human/policy gates remain visible rather than being filled automatically.

| Date | Delivery | Lead |
|---|---|---|
| 3 Nov | K01 source registry and K02 outcome/scope map; shortlist first 25 cards | R2/R6 |
| 4 Nov | K03 extraction audit and K04 claim normalization; one complete chapter slice | R2/R6 |
| 5 Nov | K05 math/domain checks and exceptions across all three chapters | R2/tools |
| 6 Nov | K06 safe retrieval corpus; K07 glossary, 100 retrieval probes and 200 contextual dev messages | R1/R3/R6 |
| 7 Nov | K08 candidate export, actual three-chapter graph integration and guard traces | R3/R4/R6 |
| 8–9 Nov | Fix measured failures; focused teaching assessment and R5-led independent evaluation work | R1/R2/R5 |
| 10–11 Nov | Freeze accepted artifacts, record demo, document remaining limitations and submission evidence | Team |
| 12 Nov, EOD | Final submission deadline from the programme email | Team |

Priority order if capacity is tight: one complete source-to-citation-to-checker slice, then all three textbook chapters; selective exemplar enrichment follows. Reduce optional expansion before reducing source fidelity or disclosing unverified data as trusted. Do not reschedule the independent evaluation freeze casually: R5 must protect untouched cases before final runs.

## 10. First executable implementation task

Implement K01/K02 next: read the retained source manifest, produce a new source registry without changing originals, compare edition metadata and map the 25 existing concepts to exact textbook sections and current syllabus scope. Record every unresolved entry, including T08. Acceptance: nine source records with matching hashes, complete source bindings for the retained candidate concepts or explicit gaps, and no raw source text/keys in a public artifact.

Then build one vertical slice for a source-backed concept through extraction, claim checks, safe retrieval and an actual tutor citation. Use that slice to settle the schema before processing all three chapters. No new bulk download is required to begin.

## References and relationship to prior work

- Official source discovery: [NCERT textbooks](https://ncert.nic.in/textbook.php), [NCERT exemplar catalogue](https://ncert.nic.in/exemplar-problems.php?ln=en), [CBSE curriculum](https://cbseacademic.nic.in/curriculum_2027.html). Specific source URLs are listed in section 3.
- Local acquisition manifest: `socratic_tutor_dataset/sources_private/manifest.json`; today's read-only check: `Docs/knowledge_acquisition/source_inventory_audit.json`.
- Current source evidence: `socratic_tutor_dataset_v2/source_evidence_v080/`; preserve original evidence and frozen v0.10.0. Existing assistant source checks are not human approval.
- `Docs/dataset_integration_v0_2/04_ACQUISITION_PLAN.md` remains the new conversation/data collection plan; `06_EVALUATION_PROTOCOL.md` remains the independent conversational-evaluation proposal. Those additions do not replace the capstone's separate golden-case, simulated-student, security or calibration obligations.
- `Socratic_Tutor_Requirements.md` remains the recorded capstone checklist. This plan updates the acquisition/verification approach for textbook facts; historical plans and review decisions remain unchanged. No new sources, knowledge exports, human approvals or study results were created by writing this plan.
