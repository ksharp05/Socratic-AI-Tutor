# Product quality v2 — local review candidate

6 November 2026. Local **Beta**, tag `beta-product-quality-v2-candidate`. Final runtime **2af7ecf**; the completed matched live comparison and fresh baselines retain exact source **779e788**. The final revision completes one mathematical definition and is separately qualified offline. No push/PR.

The tutor now gives direct short cited concept explanations, keeps the maths request when a learner is frustrated, recognises wrapped phrases without changing stored numeric layout, and acknowledges explicit correction as information without awarding mastery. Smaller-step support asks for givens without advancing the hint. The UI restores owned active/interrupted state, locks conflicting quiz actions, and lets an unfinished quiz end without a score.

## Recorded results

| Check | Result | What it establishes |
|---|---|---|
| Final four-suite regression | **817 passed** | 165 new checks since v1, including 122 formatting/control checks |
| Same 32 public journeys live | **20/32 before → 32/32 after** | Fixed developer-authored functional targets, 42 turns/version |
| Same panel offline | **10/32 → 32/32** | Both the live-source candidate and final wording revision pass 32/32 |
| Live references | **45/45 mechanically verified** | 22 before + 23 after; semantic review remains pending |
| Current C1/C2 stub qualification | **96 sessions + 6 matching smokes** | 250 reference snapshots verified on source 779e788 |
| Final exact local CI gates | **3/3 pass** | C1, student-evaluation and security smokes on final source; no remote CI |
| Security replay | **80 cases per condition** | Guards on 0/18 measured attacks succeeded; off 1/18; 27 unsupported each |
| Assistant-operated browser | **1280/390 px checked** | Quiz refresh/exit, cited wrapped question, source panel, no horizontal overflow |

Both C1/C2 baseline arms remain at recall **0.208**, precision **0.625**, success proxy **4/48**, and mean synthetic gain **0.167**. Their identical trajectories establish no C2 or learning advantage. Sixteen shared cards with repeated seeds are not independent learners.

The live functional score includes routing/directness requirements. A failing check does not necessarily mean the mathematics was wrong. For example, the old tangent reply asked the learner to recall a definition, the common-difference reply began with unrelated first-term wording, and acknowledgements carried the tutor route without calls. Frustration sometimes swallowed the actual maths request; a topic shift could keep the previous misconception probe. All replies/traces and failures are retained. These are public development cases targeted by the implementation, not held-out final results.

## What the extra scrutiny caught

Formatting stress initially found **11 failures/48** definition variants and **8 missed flags/12** guard variants. The fix flattens only the analysis copy and preserves original redacted text and numeric line breaks. Altered source text/chapter/hash fails closed. Actual API/UI tests exercise interruption after planning and recovery without replay.

After the live panel passed, assistant transcript inspection found that the short quadratic definition omitted the highest-power-two condition present in its source card. Final revision **2af7ecf** now uses the complete existing explanation; two new regressions, all 817 tests, the 32-case offline panel and all three local CI gates pass. **No paid rerun was made:** live evidence stays attached to 779e788. This illustrates why mechanical passes cannot replace teacher review.

One combined test launch omitted the canonical data-root setting: 781 checks passed and 34 fixture setups failed. Its log is preserved; correcting the launch setting yielded 815 passes before the final wording change. The final source passes 817. Initial failures, source archives and completed experiments were preserved.

## Cost and authorization

The explicit approved OpenRouter comparison is complete: **36 requests / USD 0.0084464**, all costs provider-reported, zero errors/refusals/in-flight requests. Before: **23 calls / USD 0.0051912**; after: **13 / USD 0.0032552**. Definitions and acknowledgements now use code-owned sourced information, so the lower cost in this panel is not evidence of an architectural advantage.

Automatic approval review initially rejected transmission under the broad budget wording. The user then explicitly approved these fixed public/synthetic payloads, OpenRouter destination and model. The exact decision is in the durable receipt. No real student data was used. Both scheduled runs completed once; no further calls are scheduled, and leftovers must not fund repeats.

Phase actual spend is **USD 0.0107708** under the USD 10 ceiling; allocated batch caps total USD 0.50, with USD 9.50 unallocated. Total recorded attempts are **1,097**, known continuation spend **USD 0.2947428**, excluding the original 98 requests whose money is unknown. Four prior wallets are byte-identical.

## Data, review and next steps

The public bank has **665 items**, but only **131 graph-eligible practice items across four task families**, plus 12 AI-authored development quiz items. Eligibility is not actual teacher approval. [DATA_SUFFICIENCY.md](DATA_SUFFICIENCY.md) explains why that inventory is sufficient for engineering checks but not final effectiveness claims.

Twelve explanations use seven reference paraphrases, with original PDF hashes/pages. Coefficient help explicitly cites a Class 9 prerequisite source. All remain AI candidates awaiting actual teacher review. [LIVE_PAIRED_REVIEW.jsonl](LIVE_PAIRED_REVIEW.jsonl) contains 32 paired actual live journeys; [PAIRED_REVIEW.jsonl](PAIRED_REVIEW.jsonl) preserves the same cases offline. They are not 64 independent cases. [SOURCE_REVIEW.jsonl](SOURCE_REVIEW.jsonl) covers the final 12 explanations. All labels are blank. Follow [REVIEW_INSTRUCTIONS.md](REVIEW_INSTRUCTIONS.md).

Next: actual R3/R2 review of the candidate, supported diagnosis scope and specialist/route contract; teacher/source review; stronger connected task coverage and independent final assessment/raters; preregistration/freeze; independent installation and remote CI evidence. Original 63-item/40-item review packets and four lesson decisions remain blank. **Formal M3/M4 acceptance is not claimed.**

Use canonical `D:\Work\IITB\Socratic Tutor` as cwd, set `SOCRATES_SOURCE_WORKSPACE` to it, and run Main's Python with `scripts/product_quality/report_v2.py --check` to verify saved evidence without provider calls. Completed runners refuse existing output; do not move/delete results to bypass them. Preserve historical reports rather than regenerating v1 against changed phase allocations. Full source and budget receipts are under ignored Directions/product_quality/v2.
