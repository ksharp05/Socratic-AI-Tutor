# tutor.retrieval (R2)

NCERT ingestion and hybrid retrieval for `textbook-kb`. The spike notes and baseline numbers are in [Docs/spikes/S3.md](../../../Docs/spikes/S3.md).

## Use

```bash
# once: copy jemh104.pdf, jemh105.pdf, jemh108.pdf into data/ncert/ (git-ignored; never commit them)
python -m tutor.retrieval.ingest            # writes data/ncert/index/ and fetches the embedding model once
python -m tutor.retrieval.ingest --no-dense # BM25 only
python -m tutor.retrieval.evaluate          # development Recall@5 / MRR, report in var/retrieval_runs/
```

To switch modes, set `[retrieval] mode` in `config/app.toml`:
- `poc_cards` (the default): the POC's BM25 over the 5 cards.
- `hybrid`: everything in this package.

If no index has been built, hybrid serves the 25 cards only, and every search result carries a `notice` saying so.

## Files

| File | What it does |
|---|---|
| `sources.py` | The only PDFs that may be indexed: `jemh104`, `jemh105`, `jemh108`. Refuses `jemh1an` (answers appendix, D-4) and any other file |
| `textnorm.py` | Repairs the Symbol-font glyphs (U+F0xx) in extracted text. The maths tokenizer: θ→theta, √→sqrt, ²→^2; keeps `a_n` |
| `chunk.py` | Chunks one chapter by section (Examples kept with solutions; about 350 words max). Gives stable IDs like `ncert:jemh104:s4.3:c02` |
| `ingest.py` | `pdftotext -layout -enc UTF-8` → chunks → `chunks.jsonl`, `manifest.json`, `dense.npy` |
| `dense.py` | fastembed `BAAI/bge-small-en-v1.5` on CPU. Model cached in `data/models/`; loaded offline at query time |
| `hybrid.py` | BM25(cards) + BM25(sections) + dense, fused with RRF (k = 60). Results carry `kind`, citation fields and the source page |
| `evaluate.py` | Recall@5, MRR and group@5 on the 15 **development** card queries only |

## Rules

- NCERT text, the PDFs, the index and the model never go in git: `data/ncert/` and `data/models/` are ignored. Tests use synthetic text.
- Section results have `use_for_formulas: false`. Formulas are cited from cards (TP-T2), because extraction garbles them (S3).
- Evaluation reads only `plan_freeze(build, 0)["dev_files"]`, never held-out queries.
