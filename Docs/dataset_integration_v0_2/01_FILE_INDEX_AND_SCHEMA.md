# File index and snapshot schemas

Source root: `Directions\socratic_tutor_dataset_expanded_v0_2`. Output root: `Docs\dataset_integration_v0_2`. Source files remain unchanged.

The JSON schemas describe observed field shapes. They are not independently authored domain truth or an approval mechanism. `audit.py` separately checks provenance, joins, source status and public-prompt mathematics.

| Collection | Exact source path | Rows | Example ID | Access |
|---|---|---:|---|---|
| problems | `Directions\socratic_tutor_dataset_expanded_v0_2\dev\problem_variants.jsonl` | 232 | `SYN-P-Q01-01` | engineering_review_only |
| dialogues | `Directions\socratic_tutor_dataset_expanded_v0_2\dev\dialogues_synthetic.jsonl` | 928 | `SYN-DLG-Q01-01-SELF_REPAIR` | engineering_review_only |
| tutor_contexts | `Directions\socratic_tutor_dataset_expanded_v0_2\dev\tutor_turn_contexts_unreviewed.jsonl` | 5568 | `SYN-TURN-00001` | engineering_review_only |
| messages | `Directions\socratic_tutor_dataset_expanded_v0_2\dev\contextual_learner_messages.jsonl` | 2400 | `SYN-MSG-01-001` | engineering_review_only |
| preferences | `Directions\socratic_tutor_dataset_expanded_v0_2\critic_only\response_preference_pairs.jsonl` | 464 | `SYN-PAIR-0001` | critic_only |
| security | `Directions\socratic_tutor_dataset_expanded_v0_2\dev\security_attack_control_pairs.jsonl` | 360 | `SYN-SEC-0001` | engineering_review_only |
| references | `Directions\socratic_tutor_dataset_expanded_v0_2\review\reference_answers_dev_only.jsonl` | 232 | `SYN-P-Q01-01` | restricted_verifier_only |
| retrieval | `Directions\socratic_tutor_dataset_expanded_v0_2\review\retrieval_candidates_unlabelled.jsonl` | 87 | `RET-CAND-001` | engineering_review_only |
| glossary | `Directions\socratic_tutor_dataset_expanded_v0_2\review\glossary_unreviewed.jsonl` | 90 | `G-001` | engineering_review_only |
| seed_misconceptions | `Directions\socratic_tutor_dataset_expanded_v0_2\parent_seed_v0_1\dev\misconceptions.jsonl` | 30 | `Q01` | engineering_review_only |
| quarantine | `Directions\socratic_tutor_dataset_expanded_v0_2\quarantine\T08_curriculum_unconfirmed_dialogues.jsonl` | 32 | `SYN-DLG-T08-01-SELF_REPAIR` | quarantine_only |

## Typed fields and joins

All files use JSON objects, UTF-8 and stable string IDs. Status, scope, split and origin remain separate fields. Private reference values never appear in these reports. The full observed key/type definitions are under `schemas/`.

- `dialogues.problem_id`, `preferences.problem_id`, `security.problem_id`, `references.problem_id` and `tutor_contexts.problem_id` resolve to `problems.id`.
- `messages.context.problem_id` resolves to `problems.id`; its active problem text must match. `misconception_id`, chapter and family must agree. The original family mismatches are a reported defect, not silently accepted.
- `tutor_contexts.dialogue_id` resolves to `dialogues.id`; its context and candidate reply reproduce the exact dialogue prefix and next tutor turn. These 5,568 rows are dependent views.
- `misconception_id` joins the 30-record seed catalogue. `T08` is absent from the active 29 IDs and retained separately in quarantine. These IDs do not automatically join the canonical `qe_m`, `ap_m`, `tr_m` IDs.
- Keep both `variant_family` and `paraphrase_family`. Never derive a final held-out set by shuffling their members.
- The 464 preferred/rejected pairs remain critic-only; the word preferred is not a human approval. The 87 retrieval candidates have null gold IDs and are not a measured retrieval benchmark.

## Derived paths

- Metadata-only message derivative: `Directions\_integration_work\2fb0ffbb67ae8e5c\derived_v0_2_1`. Its receipt binds each original/revised row and lists the only changed field.
- Corrected inventory: `corrected/intent_catalogue_v0_2_audit.csv`.
- Review queue: `03_REVIEW_QUEUE.csv`; blinded rater views: `review_views/rater_A.csv` and `rater_B.csv`. Routing is kept under the ignored Directions work area.
- `approved_export_manifest.json` intentionally lists zero approved examples. A future runtime projection contains only example ID, chapter and reviewed messages, protected by a server-pinned manifest.

## Actual source map

| Component | Exact current entry point |
|---|---|
| Team application | `src\tutor\app.py` (`TutorApp`, `TutorState`, planner, tutor, grader, quiz, buffered output guard) |
| Model provider | `src\tutor\llm.py` (`LLM._chat`, `complete`; configured model `openai/gpt-4.1-mini`) |
| Configuration | `src\tutor\config.py` and `config/app.toml`; credential values never exported |
| Tools and state | `src\tutor\toolbus.py`, `store.py`, `mathcore.py` |
| Knowledge content | `content\poc`; full public candidate copies in `content/dataset-v0.10.0/` |
| HTTP and UI | `src\tutor_api\main.py`; `ui\app.py` (role/token UI, streaming chat) |
| Isolated candidate | `src\v02_integration\runtime.py` (`ContextualPreviewTutor`) |

HTTP/UI enablement was not performed. The live probe calls the graph directly in isolated development state. Existing API authentication remains the team component and is not replaced by this adapter.
