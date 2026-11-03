# Textbook ingestion and retrieval

The local pipeline extracts and indexes source material for the supervised beta. See the [dataset report](../datasets/DATASET_REPORT.md), [source catalogue](../datasets/NCERT_CATALOGUE.md), and [beta guide](../beta/README.md) for scope, limits and how to run and extend the system.

Implementation: `src/ncert_pipeline/`; tests: `tests_book_pipeline/`; explicit live provider probe: `scripts/book_pipeline/probe_live.py` (may incur cost). Source PDFs, extracted text and local indexes are excluded from Git. Use official NCERT sources and check permissions before redistribution.

Passage extraction and automated checks do not establish teaching quality, source fidelity or human approval. Equations, tables, diagrams and non-English material need separate processing and review; do not expose answer appendices in learner retrieval.
