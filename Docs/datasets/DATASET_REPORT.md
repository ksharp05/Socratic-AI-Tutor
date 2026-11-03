# Dataset report

Inventory date: 3 November 2026. This report describes the local materials and the beta integration, not a claim that all material is classroom-ready. See the [full book catalogue](NCERT_CATALOGUE.md) and [beta guide](../beta/README.md).

## What we have

| Dataset or asset | Size and coverage | Status and purpose |
|---|---|---|
| NCERT textbook source collection | 145 selected volumes, 1,605 usable PDFs, 25,175 known pages; classes 8–12 and common XI–XII books | Official source books across maths, science, languages and other subjects; local source collection. Book availability does not mean every book is indexed or taught. |
| Source languages | English: 93, Hindi: 21, Sanskrit: 11, Urdu: 20 volumes | Language counts are catalogue-inferred. English teaching is the current supported path; other-language originals need processing and evaluation. |
| Beta3 knowledge index | 10,878 passages/references from 86 books in 53 grade/subject combinations | Source-linked retrieval candidates for English-first concept conversation; not proof of passage correctness or review. |
| Class 10 maths practice | 665 items: 160 Quadratic Equations, 320 Arithmetic Progressions, 185 Introduction to Trigonometry; 17 task families | Public practice with staged hints and code-checked answer forms. The three chapters are the strongest supported maths scope. |
| Earlier maths development build | 1,379 records: 665 practice, 160 development, 450 internally authored held-out candidates, 104 quiz | Counts describe an earlier development build, not additional independent evaluation. Candidate held-out cases were authored internally. |
| Expanded conversational development data | 232 problems; 928 synthetic dialogues and 11,136 turns; 5,568 tutor contexts; 2,400 learner messages | Unreviewed development data, useful for exploring language and tutoring interactions. Not evidence of human-reviewed teaching or production training readiness. |
| Preference, safety and retrieval development data | 464 critic-only preference pairs; 360 attack/control pairs; 87 unlabelled retrieval candidates; 90 draft glossary entries; 32 quarantined T08 dialogues | Development and review material. Quarantined material is excluded; preference and security records are not validated outcome claims. |
| Beta scenarios | 34 development scenarios | Most recent run recorded 28 technically completed supported scenarios and six appropriate unsupported/clarification cases. This is not an independent measurement of factual or teaching quality. |

Beta3 index kinds as recorded in the database:

| Kind | Records |
|---|---:|
| extracted_prose_preview | 10,851 |
| normalized_math_reference | 25 |
| source_prose | 2 |

Counts above are of different assets and must not be added together: extracted passages derive from source books; some practice and evaluation sets share a development lineage. The catalogue includes five common XI–XII volumes applicable to both classes, without double-counting them as unique books.

## How data supports communication

The language model handles ordinary English conversation, explains concepts, asks follow-up questions and adapts to the learner's messages. The retrieval index supplies source-grounding; it is not a corpus of natural conversations. The synthetic dialogues are separate, unreviewed development examples, not proof that a model needs or has been fine-tuned. For the three Class 10 maths chapters, the practice service supplies problems and checks supported answer shapes; free-text reasoning is not automatically scored.

## Gaps and quality limits

- Textbook extraction can damage equations, tables, layout and diagrams. A readable source page and exact source linkage do not guarantee that a retrieved passage is a sound lesson or that the model's response follows it.
- Class 9 ICT is listed as coming soon; one Class 11 Urdu asset is malformed; Class 12 Urdu catalogue/edition coverage remains unresolved. The known usable page count is not a complete count of every publisher asset.
- Additional classes and subjects have source coverage but not the same code-checked maths-practice support. Hindi, Sanskrit and Urdu originals are not enabled as supported teaching languages in the current English-first beta.
- Synthetic dialogues, labels, lessons and candidate cases require appropriate human content review. Final evaluation needs independently authored or otherwise independently curated held-out cases, separate from tuning; textbook facts and mathematical checks alone do not establish instructional quality.
- No learning-gain study, representative learner study, independent factual-accuracy benchmark or production-readiness certification is claimed. Continue supervised beta testing.

## Access and provenance

The collection was acquired from the [official NCERT textbook portal](https://ncert.nic.in/textbook.php). The [catalogue](NCERT_CATALOGUE.md) lists volume codes and titles. Textbooks, extracted full text, local indexes, private evaluation material and private grading keys are excluded from Git; each collaborator needs an authorized local data setup. The repository includes public practice items and selected development test cases. Check publisher terms before redistributing source text or derivatives. Source hashes and detailed acquisition and extraction records remain with the local collection.
