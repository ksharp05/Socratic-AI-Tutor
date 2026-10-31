"""NCERT ingestion and hybrid retrieval (R2).

- `sources`: the only PDFs that may be indexed (chapters 4, 5 and 8; never the answers appendix, D-4).
- `textnorm`: Symbol-font repair for extracted text and the maths tokenizer shared by every BM25 index.
- `chunk`: splits extracted pages into section chunks with stable passage IDs.
- `ingest`: `python -m tutor.retrieval.ingest` writes the index to data/ncert/index/ (git-ignored).
- `hybrid`: BM25 over cards + BM25 over sections (+ optional dense vectors), fused with RRF.
- `evaluate`: Recall@5 and MRR on the development card queries only.
"""
