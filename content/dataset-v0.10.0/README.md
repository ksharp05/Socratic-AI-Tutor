# Tutor-visible content from dataset v0.10.0

Byte-identical copies of the files the tutor is allowed to see. Each SHA-256 in `MANIFEST.json` matches the frozen build's `metadata/files.sha256.json` (payload `49862eea…`).

| File | Records | What it is |
|---|---|---|
| `concepts.jsonl` | 25 | Concepts and their prerequisite graph (QE, AP, trigonometry) |
| `misconceptions.jsonl` | 30 | The shared misconception catalogue: wrong rule, probe, hint ladder |
| `corpus.jsonl` | 25 | One short teaching card per concept, with its NCERT anchor. Our own writing, not textbook text |
| `practice_questions.jsonl` | 665 | Practice items with typed problems and 3-stage hints. **No answer keys**: `math-tools` computes them |
| `grading_contract.json`, `answer.schema.json` | – | The typed-answer format and grading contract |
| `export_manifest.json` | – | The dataset's own statement: no keys, no student cards, no generator code |

> [!WARNING]
> **Unapproved development preview.** Every record is `pending_human_review`. Nothing here counts as teacher-approved, and the tutor must still go through the approval gate before publishing practice sets.

## What is not here, and why

| Kept out of git | Who holds it |
|---|---|
| Held-out benchmark cases, held-out simulated students (`candidate_final`), held-out retrieval queries | R5 only, frozen with hashes (separation rule 1) |
| Development simulated students, quiz pairs, development benchmark cases, attacks and controls | R5 shares the development part in `eval/` once the held-out freeze is recorded |
| NCERT PDFs, page images, text derived from the textbook | Each member downloads the PDFs locally; ingestion reads them from `data/ncert/`, which git ignores |

The POC uses only a five-concept slice of this data, in `content/poc/` and `eval/poc/`.
