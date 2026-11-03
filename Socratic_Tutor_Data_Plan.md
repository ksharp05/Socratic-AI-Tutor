# Socratic Tutor - Data Inventory and Acquisition Plan

Prepared 20 October 2026. This is a proposed technical plan, not a claim that datasets have been collected or validated.

Implementation update, 24 October 2026: current candidate `socratic_tutor_dataset_v2/builds/v0.10.0/` preserves all 1,379 questions, 52 quiz pairs, 25 references, 40 target-complete learner assignments and existing security/source assets. It adds 610 private benchmark contracts and opaque solver inputs, four schemas, recorded action/citation checks and a failure-aware scoring CLI. All 64 tests, full validation, deterministic reproduction of 158 payload files and separate offline validation passed. All 2,469 reviews remain pending. Actual model runs/teaching outcomes, semantic labels, independent final authorship and human approvals remain absent. Earlier frozen builds and reports are preserved. The plan below remains a historical proposal; its quotas are not extra guide requirements.

Confirmed scope: **Class 10 Maths - Quadratic Equations, Arithmetic Progressions, Introduction to Trigonometry**. Proposed initial language: English. The guide's general requirements and Tutor brief still apply.

The proposed first version uses retrieval, structured teaching data and synthetic learners. No additional model pretraining or fine-tuning dataset is required by the capstone guide. Most project-specific data must be authored, checked and versioned by the team.

## 1. Sources verified

These official URLs were opened successfully on 20 October 2026. Record the actual edition and checksum during collection; a stable URL can later serve a different file.

| Topic | NCERT textbook | NCERT exemplar |
| --- | --- | --- |
| Quadratic Equations | [Chapter 4](https://ncert.nic.in/textbook/pdf/jemh104.pdf) | [Unit 4](https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep204.pdf) |
| Arithmetic Progressions | [Chapter 5](https://ncert.nic.in/textbook/pdf/jemh105.pdf) | [Unit 5](https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep205.pdf) |
| Introduction to Trigonometry | [Chapter 8](https://ncert.nic.in/textbook/pdf/jemh108.pdf) | [Unit 8](https://ncert.nic.in/pdf/publication/exemplarproblem/classX/mathematics/jeep208.pdf) |

Additional sources:

- [CBSE Class 10 Maths syllabus, 2026-27](https://cbseacademic.nic.in/web_material/CurriculumMain27/SecPart1/Maths_SecP1X_2026-27.pdf): authoritative scope and learning outcomes. It covers real-root quadratic equations, APs and introductory trigonometry. Use only the selected chapter scope; the full syllabus is not an instruction to implement all Maths topics.
- [CBSE Maths Standard sample question paper, 2026-27](https://cbseacademic.nic.in/web_material/SQP/ClassX_2026_27/MathsStandard-SQP.pdf) and [marking scheme](https://cbseacademic.nic.in/web_material/SQP/ClassX_2026_27/MathsStandard-MS.pdf): references for question styles, mathematical steps and partial-credit design. Use selected relevant material; they are not a ready-made tutoring evaluation set.
- [NCERT exemplar catalogue](https://ncert.nic.in/exemplar-problems.php?ln=en): official navigation and fallback discovery.
- [SymPy equation solver documentation](https://docs.sympy.org/latest/modules/solvers/solveset.html) and [simplification documentation](https://docs.sympy.org/latest/tutorials/intro-tutorial/simplification.html): implementation references for code-based answer checking, not curriculum sources.

Source-use constraint: the capstone guide explicitly says to use NCERT material within the project and not redistribute its PDFs. The [published ePathshala textbook notice](https://epathshala.nic.in/wp-content/doc/book/btextbook/textbook.htm) also contains restrictions on redistribution and software/content packaging. Treat these materials as copyrighted, not openly licensed. The domain lead should clarify the permitted capstone use with the programme before incorporation into software/distribution; a private folder or `.gitignore` is not itself permission. Do not package source PDFs, extracted book text or populated indexes in public repositories/images. Original team-authored material can progress independently while this use question is resolved. This plan does not assume permission for public hosting or commercial reuse.

## 2. Data inventory

"Guide" means specified in the capstone guide. "Proposal" means a planning choice, which can change without changing the guide.

| Data asset | Purpose and source | Quantity | Format and owner |
| --- | --- | --- | --- |
| Source manifest and syllabus map | Pin the curriculum, provenance, edition and permitted use; official URLs above | Proposal: 1 syllabus, 6 chapter/unit PDFs, 1 sample-paper/marking-scheme pair | JSON/CSV; domain lead + knowledge engineer |
| Teaching corpus | Ground hints in NCERT sections and exemplars; manually verify equations and referenced diagrams | Guide: selected 3 chapters; chunk count determined by content, not a quota | Passage JSONL plus local source files; knowledge engineer |
| Concept/prerequisite graph | Drive diagnosis, mastery and next-step planning; team-authored from syllabus/textbook structure | Guide: about 25 concepts; proposal: roughly 8 quadratic, 8 AP, 9 trigonometry | YAML/JSON; domain lead + knowledge engineer |
| Misconception catalogue | Map wrong reasoning to diagnostic probes and useful hints; teacher/team authors, optional LLM drafts | Guide: 8-12/chapter; proposal: 30, 10/chapter | JSONL; domain lead with teacher/reviewer |
| Approved practice bank | Supply varied questions and graded hints; original team-authored items, informed by official sources | Proposal: 120 items, 40/chapter, spanning difficulty and concepts | Question JSONL/SQLite, restricted grading records; domain lead + tools engineer |
| Solver/checker fixtures | Validate answer keys, accepted forms, domains, numeric tolerance and malformed inputs | Proposal: cover every supported checker type and important boundary, not only a fixed count | JSONL + checker tests; tools engineer |
| Golden evaluation cases | Measure grading, diagnosis, citations, planning and expected tool behaviour; independently authored by evaluation owner | Guide: at least 60; proposal: exactly 60 initially, 20/chapter, split 20 development / 40 held-out | Evaluator-only JSONL; evaluation engineer, domain lead reviews |
| Retrieval relevance labels | Measure Recall@5 against known supporting passages; manual labels over the frozen teaching corpus | Guide: 30+ queries; proposal: 36, 12/chapter, split 12 development / 24 held-out | Query JSONL + relevance judgments; evaluation engineer |
| Hidden simulated-student cards | Model prior knowledge, persona and 1-2 seeded misconceptions for teaching experiments | Guide: 40 students; proposal: 16 development / 24 held-out | Simulator-only JSONL; evaluation engineer |
| Matched pre/post quiz forms | Measure quiz improvement without reusing the exact taught question; independent, solver-verified equivalent forms | Proposal: 3-5 questions per form/session, with matched concept/difficulty coverage; reusable within the same split | Evaluator-only questions/keys; evaluation engineer |
| Human rubric and labelled transcripts | Calibrate the different-family judge and assess teaching, grounding and answer leaks | Guide: teacher's rubric on 20 transcripts, and 20+ human-labelled outputs for judge calibration | Rubric YAML + label JSONL; domain/teacher input + evaluation engineer |
| Security and clean-control cases | Test answer extraction, injection, privacy, approval and minor-safety behaviour; author independent of defence builder | Guide: 30+ attacks; proposal: 30 attacks + 30 comparable benign cases | Evaluator-only JSONL; evaluation engineer |
| Learner state and interaction events | Store inferred mastery, observed misconceptions, helpful explanations and session history | Generated during synthetic sessions; a few clearly synthetic demo learners initially | SQLite/Postgres and LangGraph store; knowledge + orchestration engineers |
| Question proposals and approval records | Prove only the approved version is published and edits invalidate approval | Generated by application; seed approve/edit/reject examples | SQLite/Postgres; tools/control engineer |
| Reviewed teaching lessons | Reflexion playbook by misconception, with applicability and review decisions | Generated from development failures; include at least one rejected lesson and reason | Versioned lesson records + LangGraph store; orchestration engineer, human reviewer |
| Run traces, metrics and experiment records | Reproduce E1-E4 and report failures, cost, latency and outcomes | Every run, including failures/timeouts; repeat final comparison three times | JSONL/trace backend + metrics; operations + evaluation engineers |

No real student names, school records or historical student conversations are needed for the initial capstone version. Real-user data is an optional later pilot with the required consent and policies.

## 3. Content design and mathematical checks

### Teaching passages

Each passage should include:

`passage_id`, `document_id`, `source_url`, `edition`, `retrieved_at`, `class`, `subject`, `chapter`, `section`, `pdf_page`, `printed_page`, `concept_ids`, `text`, `math_latex`, `diagram_refs`, `source_hash`, `review_status`.

Use stable IDs so citations, retrieval labels and reports refer to the same evidence. Keep printed and PDF page numbers separately. Split at definitions, explanations and example boundaries rather than blindly cutting equations at a token count. Use native PDF extraction first; apply OCR only where extraction fails. Inspect every extracted formula and retained diagram used by the system.

### Concepts and misconceptions

Concepts need IDs, prerequisites, learning outcomes, supporting passage IDs and mastery criteria. Check the prerequisite graph for cycles and unreachable nodes. Small prerequisite explanations can be original team-authored support notes, labelled as such; avoid silently expanding into additional full chapters.

For every misconception store:

`misconception_id`, `concept_id`, `incorrect_rule`, `example_wrong_work`, `diagnostic_probe`, `distinguishing_evidence`, `hint_ladder`, `correct_reasoning`, `source_or_author`, `reviewer`, `review_status`.

Examples of candidates to review, not claims about observed student prevalence:

- Quadratics: keeping only the positive root after solving a squared equation.
- AP: using `a + n*d` where the index convention requires `a + (n-1)*d`.
- Trigonometry: treating opposite and adjacent as fixed sides when the reference angle changes.

An LLM can draft candidates; mathematical correctness and teaching suitability need human review. Record synthetic mistakes as synthetic, rather than claiming they came from real students.

### Practice items and grading

Every practice item needs an ID/family ID, concept tags, difficulty, prompt, assumptions, source/provenance, review status, hint stages and a grading/checker reference. For the proposed 120 items, aim initially at 40/chapter with 12 easy, 20 medium and 8 harder items per chapter; adjust difficulty after review. This is a proposed distribution, not an exam blueprint.

Keep practice grading keys in the grading service, separate from the tutor's searchable corpus. Expose a narrow checking tool returning an assessment and safe feedback. Hidden evaluation gold must never be exposed through this tool.

Checks must handle:

- Quadratics: nonzero leading coefficient, real-root domain for this curriculum, both roots, repeated roots, substitution checks and contextual restrictions.
- AP: one-based indexing, positive integer term counts, negative/zero common difference and agreement between enumerated and formula-based sums.
- Trigonometry: degrees versus radians, exact fractions/radicals, angle assumptions, undefined ratios and denominator restrictions.
- Algebraic proof: numeric spot checks alone are not proof of an identity. Symbolic equivalence checks must respect domains; the validity of a student's reasoning steps may still require a rubric.
- Unsupported/undecidable inputs: report an unverified result or escalate; do not silently count a solver's inability as proof the student is wrong.

Use tested Python/SymPy checkers and independent human verification for gold answers. Do not treat an LLM-generated answer as verified ground truth.

## 4. Evaluation structure and information boundaries

### Golden question split

Proposed allocation:

| Chapter | Development | Held-out | Total |
| --- | --- | --- | --- |
| Quadratic Equations | 7 | 13 | 20 |
| Arithmetic Progressions | 7 | 13 | 20 |
| Introduction to Trigonometry | 6 | 14 | 20 |
| Total | 20 | 40 | 60 |

Across each chapter include correct answers, plausible wrong work, explanations, diagnosis, under-specified problems, mathematical boundaries and appropriate tool use. Balance these with difficulty. Write expected outcomes before runs.

Assign a `family_id` to related templates, paraphrases and numeric variants and split at family level. Held-out problems should not merely be number changes of practice-bank items or development questions. The evaluation owner independently authors held-out cases and checks near-duplicates against the teaching examples, practice bank and development cases. Curriculum concepts naturally overlap across splits; the restriction concerns exposure to the test cases/answers and related variants, not banning shared subject knowledge.

For a question record, the app receives the task input and permitted observable history. The evaluation process retains expected answers, required/prohibited actions, relevant passage judgments and scoring rules.

### Retrieval labels

For the proposed 36 queries, include conversational paraphrases, notation variants and misconception-driven requests. Label all acceptable supporting passages or equivalent passage groups rather than assuming only one chunk is relevant. Retain corpus version and passage IDs. Tune retrieval on the 12 development queries; evaluate the fixed before/after configurations on the 24 held-out queries only after freezing. Do not inspect held-out failures and keep calling subsequent changes unseen evaluation.

### Simulated students and quiz forms

For each of the 40 cards store a pseudonymous ID, split, hidden mastery state, 1-2 misconceptions, response style, learning/response rules and random seed. Build coverage across all three chapters and varied starting abilities.

The simulator alone receives the hidden card. The tutor's learner model must come from observable interaction, not an oracle copy of the simulator's true misconceptions/mastery. For memory-off/on comparisons, provide the same legitimate prior interaction opportunities and control other differences.

Use matched pre/post forms testing the same concepts at similar difficulty, with different questions and answer keys. Keep them separate from practice material and use development/held-out forms within the matching split. Reuse forms across students in the same split when appropriate; do not introduce arbitrary hundreds of unique questions merely to fill the student count.

Specify and version the simulator's learning/response policy, model, seed and turn budget; hold them fixed across comparisons. Measure solver-checked quiz performance and observable behaviour, not only the simulator's claim that it learned. Report these as simulated teaching outcomes.

### Human labels and judge calibration

Create a teacher-informed rubric covering mathematical correctness, grounding, misconception handling, usefulness of hints, answer leakage and adaptation. Label at least 20 outputs by hand and apply the rubric to 20 transcripts. These records may overlap if one collection genuinely satisfies both obligations; state the overlap and retain human labels. A second human can review a subset and resolve disagreements as a proposed quality measure.

Use development/calibration sessions for judge calibration, not final held-out student sessions. Record the label scale before scoring and report the appropriate Cohen's kappa/agreement for the specified label task. The judge must use a different model family from the tutor under the guide.

### Attacks and benign controls

Proposed 30 attacks: five each for mode/role impersonation, injection through homework/retrieval, answer-key leakage, cross-learner memory access, question-publication/approval bypass, and personal-data/minor-safety boundary violations. Write corresponding benign controls so legitimate work blocked by defences can be measured.

Keep poisoned passages and attack fixtures out of the normal teaching index. Inject them into isolated test copies or controlled requests. The evaluation owner authors the attacks independently of the defence builder. Add practical tool-input boundary cases to checker fixtures as well.

### Physical access separation

Suggested logical layout (paths are a proposed structure, not created directories):

```text
content_local/               # permitted source files and extracted text; private
content_processed/           # approved teaching passages and public-to-agent metadata
teaching/                    # concepts, misconceptions, policies, approved practice prompts
grading_service_private/     # practice keys and checker specifications
evaluation_private/          # evaluator-owned, NOT mounted into the tutor container
  development/
  heldout/
  simulator_cards/
  quiz_forms/
  retrieval_labels/
  attacks_and_controls/
runtime_private/             # learner DB, checkpoint DB, proposal/approval audit
results_private/             # complete traces and raw run results
reports/                     # reviewed aggregates and redistributable submission outputs
```

A folder name is not access control. Mount only the required teaching/runtime data into the application and restrict tools to those stores. The evaluator/simulator runs separately and injects only the permitted task/student messages. Remove keys, hidden cards and learner data from application images, logs, tool outputs and public artifacts.

## 5. Runtime and improvement data

Learner-state records should include pseudonymous learner ID, concept ID, inferred mastery, confidence/evidence, misconception observations, useful explanations and timestamps. Keep interaction events so updates can be explained. Define correction/deletion and retention behaviour before collecting any real-user data.

Question proposal/approval records need proposal ID, content version/hash, proposer, teacher identity, approve/edit/reject decision and time, and published version. Do not collect an approval against a mutable question identifier alone. Internal mastery writes use the tutor brief's documented approval exception.

Start the playbook empty. Development failures can create candidate lessons with misconception tags, applicability, source run ID and reviewer decision. Preserve accepted and rejected lessons, freeze an exact playbook version before held-out tests and associate every result with that version.

Every run should capture dataset/split/family IDs, corpus version, configuration hash, exact models, prompts, playbook version, permitted learner history, tool calls, outcomes, error/timeout status, tokens, cost and latency. Store raw records even for failures; publish reviewed aggregates without student information or hidden answers.

## 6. Proposed sequence and owners

These are proposed milestones, not programme deadlines. Work by team members can proceed concurrently while preserving the required author independence.

| Dates, 2026 | Work | Owner and acceptance point |
| --- | --- | --- |
| 21 October | Freeze selected curriculum/language, schemas, IDs, role ownership and split rules; create manifest; resolve intended source-use scope | Domain + knowledge + evaluation owners; approved scope and access plan |
| 22-23 October | Collect permitted source versions, parse and review equations/figures; deliver one quadratic concept through retrieval/checking; draft concept graph | Knowledge + tools + domain; accurate citations and one checked development interaction |
| 24-27 October | Complete graph/misconceptions/practice bank; independently author gold, retrieval labels, student cards, quiz forms and attacks | Domain/teacher + knowledge for teaching data; evaluation owner for test data; reviewed coverage and family splits |
| 28-30 October | Validate schemas, answer keys, duplicates, permissions and corpus provenance; load stores and integrate dataset loaders | Tools + knowledge + deployment; clean data load and no evaluator-file exposure |
| 31 October-4 November | Run development sessions; obtain 20 rubric transcripts/20+ labels; calibrate judge; generate/review lessons; check alerts and traces | Orchestration + evaluation + domain; trustworthy development measurements |
| 5 November | Freeze corpus, held-out manifests, simulator policy, quiz forms, playbook, prompts and experiment configs | Evaluation owner signs dataset versions; no further tuning against held-out data |
| 6-9 November | Execute required controlled experiments and repeated final comparisons; retain failures and variability | Evaluation + operations; reproducible results |
| 10-11 November | Finalise evaluation report, source-use exclusions, reproducibility check and demo evidence | All six; reviewable submission package |
| 12 November | Final submission by EOD, as set by the email | Programme deadline |

If progress changes, preserve the isolation, human review and freeze requirements rather than silently using held-out data for development. Disclose any test set promoted to development and use newly independent cases for subsequent held-out claims.

## 7. Data readiness checks

- All selected curriculum concepts have supporting passages and reviewed question coverage.
- Every source file has URL, retrieval time, edition, checksum and use status; every citation resolves to a real passage/page.
- Every used equation and diagram survives extraction accurately.
- The prerequisite graph is coherent and supports the planner's next-step choices.
- Every approved practice item and golden case has a checked answer/domain or an explicit explanation rubric.
- Related question families do not cross the development/held-out boundary; hidden evaluation data is inaccessible to the app.
- Student-card ground truth cannot leak into the learner store or tutor messages.
- Attacks are isolated from the clean corpus, and corresponding clean cases support false-block measurement.
- Human labels and judge decisions are retained separately, with labels established before judge comparison.
- Versioned source, split, configuration, lesson and result records support rerunning the comparisons.

Suggested first implementation milestone: one original quadratic practice question, its source passage, one reviewed misconception, a solver check and two synthetic observable learner histories that lead to different hints. This is a small development slice while the evaluation owner independently prepares the hidden datasets.

## 8. Requirements provenance

Capstone-specific counts and constraints come from `D:\Work\IITB\Socratic Tutor\reference\Capstone_Project_Guide.pdf`, especially pages 3, 5-6 and 11-12, plus the programme email for dates. The 120 practice items, 36 retrieval queries, 30 misconceptions, 16/24 student split, 30 benign controls and milestone dates are proposals. They are not additional instructor requirements.
