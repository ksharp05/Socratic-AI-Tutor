# R4 worked-example improvement

The v2 renderer explains each calculation, completes zero-product equations and ends with a task-specific transfer question. Checked steps bind the displayed text; existing role/scope/quiz/answer guards remain enforced. Natural sentences replace mixed notation such as division by the word two. Versioned example IDs prevent reuse under an older renderer.

| Check | Before | After |
| --- | --- | --- |
| AI mean clarity, same 18 examples (1-5) | 2.611 | 4.389 |
| Known wrong controls flagged by AI | 8/12 | 7/12 |
| Originals verified by code | 18/18 | 18/18 |
| Altered controls rejected by code | 12/12 | 12/12 |

Paired AI clarity: 17 higher, 1 unchanged, 0 lower, with the same public prompts and example numbers. Each round has one unbound issue quote. The reviewer misses four controls before and five after, and some issue labels contradict their explanations. Its clarity preference is development feedback, not a reliable mathematical or teaching gate. Raw errors are preserved. Human reviews remain zero.

All 331 public practice items retain verified, different-answer examples passing the production active-item guard. The same 900 seeded inputs were replayed: 892 valid examples pass a separate oracle; eight invalid inputs are rejected. Repeated regression inputs are not independent learner observations. Boundary regimes are still not guaranteed to match; teacher review and R3 integration remain open.

The overview now shows learners only their own revisit counts by chapter. Teachers can inspect the earliest 100 item references without internal hashes. Counts include every eligible current-version row; deletion removes them. Reading cannot publish, grade or start a question. R3 still needs to persist session revisit marks and recheck publication before resuming an item.

Both capped review batches completed once: 60 calls / USD 0.02083425, with every cost reported. Phase reported spend: USD 0.09403805; accounted: USD 0.14413205, including the preserved unknown-cost reservation. The USD 10 ceiling holds; wallets are closed. Only public/synthetic material was sent.

Reproduce offline: scripts/product_quality/report_r4_iteration.py --check. Raw evidence and blank v2 teacher forms stay under ignored Directions. Earlier reports retain their original sources/cost snapshots.
