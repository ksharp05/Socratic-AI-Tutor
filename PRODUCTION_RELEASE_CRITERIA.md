# Production Dataset Release Criteria

The existing v0.1 package is a draft. Correct numerical keys alone do not establish a production tutoring dataset. This document records the objective gates for the replacement dataset, preserving the three selected Class 10 Maths chapters.

## Computational release gates

- Each question has a typed, complete problem specification, explicit assumptions and requested answer type; its displayed prompt is reproducibly rendered from those givens.
- Every answer is exact where the curriculum permits exactness, with domains, units, multiplicity and contextual restrictions represented explicitly.
- Two computational routes check every calculable answer. One route must not simply evaluate the generator's derived expression again.
- Worked solution steps have machine-checkable claims; valid final answers do not excuse invalid intermediate steps.
- Every served formula has a declared domain and a symbolic proof or exact exhaustive check appropriate to that formula. Numeric sampling alone is not an identity proof.
- Equivalent correct answers, wrong answers, omitted roots, extra roots, duplicate roots, missing units, invalid domains and malformed expressions have explicit grading behaviour and regression coverage.
- The three chapters cover all selected concepts and 30 misconception targets with operational question coverage, not only tags.
- Practice, development benchmark and assessment forms use honest family grouping. Final quiz forms are distinct cases, and no quiz item is silently reused as a benchmark question.
- Pre/post pairs have the same task structure and difficulty proxies, different givens/answers where feasible, and documented exclusions where matching is not meaningful.
- Every generated record is validated, not just a sample. Property tests explore parameter boundaries outside the shipped examples and mutation tests demonstrate that the checks detect corruption.
- Student cards, answer keys, scoring metadata and generation code cannot enter the runtime corpus export. Export contents are validated by allowlist.
- Evaluation outcomes/action expectations are frozen before runs and bind exact request/question/state versions. The solving agent receives the legitimate request data it needs, while private oracles/keys remain isolated. Recorded tool/state checks must not treat agent self-reports or missing observations as proof of safety; semantic uncertainty remains visible.
- Benchmark observations bind one model/configuration/corpus version. Retrieval outputs match frozen served text and explicit curriculum filters; structured citations resolve to valid recorded retrieval. Numeric correctness remains separate from semantic support. Missing/error/timeout/incomplete cases remain scheduled, incomplete accuracy is withheld and missing latency/token/cost metadata are not imputed as zeros. Self-reported traces do not establish trusted capture.
- Reproducible builds, strict schemas, deterministic seeds, hashes, versioned manifests and a clean-environment test command are provided. Builds preserve reviewed versions.

## Source and content gates

- Official source files retain provenance, edition, hashes and source-use status.
- Raw PDF text with unresolved fraction/superscript/diagram extraction is quarantined, not marked normalized or served.
- The production candidate corpus uses mathematically checked normalized content with accurate source anchors and explicit authorship. Diagram-dependent tasks carry a usable diagram or complete textual givens.
- Full worked solutions and private keys are separate from hint-facing content. Mode restrictions are represented and tested.
- Retrieval relevance data has explicit supporting evidence and recorded label provenance; proposed labels must not be called human labels.
- Retrieval proposals cover the full frozen passage catalogue, distinguish partial from sufficient support and record alternatives/combinations. Text/domain changes invalidate semantic annotations. Recall denominators retain scheduled failed/missing queries and ranking inputs bind exact query/corpus versions; test scores are not measured retriever performance.

## Limits arithmetic cannot remove

- Human teacher approval of publication and the required rubric/labels must not be fabricated.
- Independent held-out authorship must be established by the independent evaluation owner; the assistant cannot make cases unseen to itself by moving files or renaming families.
- Measured teaching effectiveness requires executed sessions and an appropriate evaluation protocol; generated fixtures are not observed outcomes.
- Source-use permission and deployed application privacy/access controls are external to a numerical answer checker.

The release report must distinguish computational dataset qualification, content approval, independent evaluation qualification and deployed-system qualification. The overall production claim remains false while any applicable gate is incomplete.
