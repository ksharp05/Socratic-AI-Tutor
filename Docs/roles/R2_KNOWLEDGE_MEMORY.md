# R2 · Knowledge and memory engineer · Rizwan Farooq

**What the guide asks** (lectures L4–L6 and L9):
- ingestion that keeps source metadata;
- hybrid search (BM25 plus vectors with RRF), a reranker and a query-side technique;
- Recall@5 on 30 or more labelled queries;
- the memory store and its one-page policy;
- a memory-on versus memory-off comparison.

## What exists

| Piece | Where |
|---|---|
| NCERT ingestion: chapters 4, 5 and 8, sections, equations kept, chapter tags | `src/tutor/retrieval/ingest.py`, `chunk.py`, `sources.py` |
| Retrieval: BM25 over cards; optional hybrid mode with BM25 over NCERT sections plus `bge-small-en-v1.5` dense vectors, fused by RRF (k = 60) | `src/tutor/retrieval/hybrid.py`, `dense.py`; `[retrieval]` in `config/app.toml` |
| Retrieval evaluation: 15 labelled queries, Recall@5 0.928 and MRR 0.836 (development) | `src/tutor/retrieval/evaluate.py`; report section 5 |
| `textbook-kb` MCP server (search, section, exemplar) | `src/tutor/mcp_servers/textbook_kb.py` |
| Learner store: mastery, misconceptions, what worked; privacy and deletion | `src/tutor/store.py`, `learner.py`, `learner_privacy.py`, `src/tutor/mcp_servers/learner_store.py` |
| Memory policy (one page) | `Docs/MEMORY_POLICY.md` |
| Memory on versus off (E4a, 16 sessions) | Report section 5 |
| Live-beta retrieval fixes on 10 Nov (stoplist, glossary, relevance floor): in-scope hits went from 67 to 75 of 92 | `src/socrates_beta/` |
| **Live-beta saved-question queue** (schema v2, 30 tests) | `src/socrates_beta/`, `tests_beta/test_revisit_queue.py` |
| **PR 8 memory review and cross-session proposal** | `Docs/m3/R2_PR8_MEMORY_REVIEW.md`, `Docs/m3/R2_CROSS_SESSION_PROPOSAL.md` |

## Who built it

| Built by | What |
|---|---|
| **Rizwan** (11 Nov; contribution log) | The saved-question queue with 30 tests on SQLite and Postgres; the review of PR 8 against the memory contract; the revisit-queue row in the memory policy; the cross-session proposal. |
| **Lakshya (Lead)**, with Claude Code | Ingestion, the retrieval package and its evaluation, `textbook-kb`, the learner store and deletion, most of `MEMORY_POLICY.md`, the 10 Nov beta retrieval fixes, and the E4a run. |

Confirm with Rizwan whether he worked on any of the Lead-built pieces. The git record shows one commit from him.

## How it works (learn the Lead-built parts)

- **Search:** `textbook-kb.search` searches the current chapter only, top 2 results. The tutor may cite only passages that were actually retrieved, and the output guard checks this.
- **Retrieval modes:** the default config is `poc_cards`. `hybrid` turns on BM25 plus dense vectors with RRF, after `python -m tutor.retrieval.ingest`.
- **What memory keeps:** mastery per concept, flagged misconceptions with their evidence, and the explanation style that worked.
- **Deletion:** a teacher deletes a learner through Data requests or `DELETE /learners/{id}`. A marker blocks all access before cleanup, and an interrupted cleanup resumes. In the live beta, "Forget my data" deletes the whole profile.

## Likely questions

- **Is retrieval hybrid, and is there a reranker?** Hybrid (BM25 plus dense, RRF) is built and configurable, and the default is the card BM25. There is no cross-encoder reranker and no query-rewriting step. Say this plainly.
- **How many labelled queries?** 15, which is below the guide's 30.
- **Did memory help?** Not in E4a: quiz change was −0.063 [−0.188, 0.000], and diagnosis recall was 0.042 both on and off.
- **How does the queue avoid leaking answers?** It stores item IDs, not answers. Only a code-checked correct answer clears it, and it is never used in quizzes.

**Files to open:** `Docs/MEMORY_POLICY.md`, `src/tutor/retrieval/README.md`, `tests_beta/test_revisit_queue.py`, `Docs/m3/R2_PR8_MEMORY_REVIEW.md`.
