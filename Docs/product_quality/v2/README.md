# Product quality v2 — local review candidate

6 November 2026. Qualified runtime: `779e788` on local **Beta**. The user asked for further improvement and rigorous testing. This candidate gives short source-backed concept explanations, keeps the maths request when a learner is frustrated, preserves message layout while recognising wrapped phrases, and restores owned quiz/interrupted-session state. An unfinished quiz can be left without scoring. Explicit self-correction is now an information action with no model call or mastery claim.

## Evidence

| Check | Result | Interpretation |
|---|---|---|
| Full four-suite regression | **815 passed** | 163 new checks since v1, including 122 formatting/control checks |
| Same 32 public journeys, 42 turns per version | **10/32 before → 32/32 after** | Offline functional targets; developer-authored, not independent evaluation |
| Panel references | **44/44 snapshots mechanically verified** | 21 before + 23 after; semantic review pending |
| Current C1/C2 stub baselines | **96 sessions + 6 matching smokes** | 250 references verified; no provider requests |
| Exact local CI gates | **3/3 pass** | C1 smoke, simulated-student smoke and security smoke; no remote CI |
| Security replay | **80 cases per condition** | Guards on: 0/18 measured attacks succeeded; off: 1/18; 27 unsupported per condition |
| Learner browser | **1280/390 px checked** | Quiz refresh/exit, cited wrapped question, readable source panel, no horizontal overflow |

Both baseline arms still have recall **0.208**, precision **0.625**, success proxy **4/48**, and mean synthetic gain **0.167**. The arms are identical on these trajectories. Better definition handling is not evidence of a C2 or learning advantage. Repeated seeds and formatting variants are not new independent learners.

The additional stress tests first found 11 failures among 48 definition-format variants and eight missed flags in 12 guard-format variants. The original receipts and pre-hardening panel remain saved. The fix analyses a whitespace-normalised copy while retaining the learner's original redacted message and numeric line breaks. Final tests include actual graph precedence for mixed safety/concept messages, altered-reference rejection, and API/UI interruption without automatic resend.

One full-suite launch omitted the canonical data-root variable: 781 checks passed and 34 fixture setups failed. That failed log is preserved; after correcting only the launch setting, all 815 passed. No product changes were made to hide those fixture errors.

## Sources and data

Twelve targeted explanations use seven new reference paraphrases. Original NCERT PDFs were inspected locally, with exact file hashes, PDF/printed pages, and a visible original-reference link. Coefficient help explicitly uses a Class 9 prerequisite source. These are AI-authored paraphrases awaiting an actual teacher's review. Original PDFs, frozen dataset content, completed studies and historical reports remain preserved.

There are **665 public practice items**, but graph eligibility currently covers **131 practice items** across four task families, plus 12 AI-authored development quiz items. Eligibility is not teacher approval. See [DATA_SUFFICIENCY.md](DATA_SUFFICIENCY.md) for the narrower connected scope and independent-evaluation gaps.

[PAIRED_REVIEW.jsonl](PAIRED_REVIEW.jsonl) has 32 paired public journeys with A/B labels and blank review fields. [SOURCE_REVIEW.jsonl](SOURCE_REVIEW.jsonl) has 12 explanations with exact source anchors and blank fields. The private A/B map stays under ignored Directions. [REVIEW_INSTRUCTIONS.md](REVIEW_INSTRUCTIONS.md) explains the intended review. Neither packet supplies actual human labels or final-study data.

## Live comparison and cost

**No new provider calls or spend.** A matched live run is prepared with a hard cap of **200 requests / USD 0.40**, allocated inside the existing USD 10 phase ceiling. Automatic approval review rejected execution because the budget statement did not explicitly authorize sending these public/synthetic payloads to **OpenRouter, openai/gpt-4.1-mini**. A destination/payload approval question is pending. No v2 wallet or live output exists, and the approval receipt now fails closed until that decision.

Phase actual spend remains **USD 0.0023244**; allocated caps total USD 0.50, with USD 9.50 unallocated. Total recorded provider attempts remain **1,061**, known continuation spend USD **0.2862964**, excluding the original 98 requests whose money is unknown. All four prior wallets remain byte-identical. Do not reuse their leftovers, reset ledgers, or rerun completed pilots/studies.

## Reproduction and next gate

Use `D:\Work\IITB\Socratic Tutor` as cwd, Main's `.venv\Scripts\python.exe`, and set `SOCRATES_SOURCE_WORKSPACE` to that canonical cwd. The safe offline verifier is `scripts/product_quality/report_v2.py --check`. It reads saved evidence, verifies frozen sources, trajectories, citations, budgets and reports, and performs no model or experiment calls. The runners refuse existing output. Do not move/delete completed result directories to bypass that protection.

The v1 report is historical. Its old generator reads the current phase allocation; regenerating it after a new allocation would rewrite history. Use this v2 verifier to check preservation instead.

Next: explicit live payload approval; actual R3/R2 review of the AI candidate and specialist/route contract; teacher/source reviews; independently authored final assessment and separate raters; final preregistration/freeze. Diagnosis coverage and narrow connected families remain product gaps. Another person's clean installation and actual remote CI failure evidence are still open. Original 63-item/40-item review packets and four lesson decisions remain blank. **Formal M3/M4 acceptance is not claimed.** No push or PR was made.
