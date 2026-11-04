"""Recall@5 and MRR on the 15 DEVELOPMENT card queries: `python -m tutor.retrieval.evaluate`.

Queries and judgments come only from the development partition, loaded in memory with
`tutor_eval.freeze.plan_freeze(build, 0)["dev_files"]`; no held-out query is read. The labels are
assistant-proposed, not human. Metrics follow the dataset's `summarize_rankings`:
- relevant = passages judged grade >= 1;
- Recall@5 = |relevant ∩ top 5| / |relevant|, averaged over queries;
- MRR = mean of 1 / rank of the first relevant passage (0 if none in the ranking, cut at 20);
- group@5 = share of queries whose top 5 contains one complete acceptable support group.

The labels judge cards only. For hybrid runs two views are reported:
- "strict": the fused list as served, where section chunks take ranks and count as not relevant;
- "cards": the same fused order with section chunks removed (what the card scorer can score).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path

import bm25s

from ..config import CONFIG_PATH, ROOT, SETTINGS
from .hybrid import HybridRetriever, build_retriever, card_text, load_cards

# The frozen build is private and not in git; point SOCRATES_SOURCE_WORKSPACE at the workspace that holds it.
DEFAULT_BUILD = Path(os.environ.get("SOCRATES_SOURCE_WORKSPACE", ROOT)) / SETTINGS.raw["dataset"]["build"]


def dev_queries(build: Path) -> list[dict]:
    from tutor_eval.freeze import plan_freeze
    rows = [json.loads(line) for line in plan_freeze(build, 0)["dev_files"]["retrieval_judgments.jsonl"]]
    assert all(r["partition"] == "development" for r in rows), "non-development query in the dev files"
    return rows


def metrics(ranked: list[list[str]], queries: list[dict], k: int = 5) -> dict:
    recalls, rrs, groups = [], [], 0
    for ids, q in zip(ranked, queries):
        relevant = {j["passage_id"] for j in q["relevance_judgments"] if j["grade"] >= 1}
        top = set(ids[:k])
        recalls.append(len(top & relevant) / len(relevant))
        rrs.append(next((1 / i for i, pid in enumerate(ids[:20], 1) if pid in relevant), 0.0))
        groups += any(set(g) <= top for g in q["acceptable_support_groups"])
    n = len(queries)
    return {"recall@5": round(sum(recalls) / n, 4), "mrr": round(sum(rrs) / n, 4),
            "group@5": round(groups / n, 4), "queries": n}


def poc_bm25_ranking(cards: list[dict], query: str) -> list[str]:
    """The POC algorithm (bm25s default tokenizer, English stopwords), over all 25 cards."""
    from ..mcp_servers.textbook_kb import _tokenise
    retriever = bm25s.BM25()
    retriever.index(bm25s.tokenize([_tokenise(card_text(c)) for c in cards], stopwords="en", show_progress=False),
                    show_progress=False)
    docs, scores = retriever.retrieve(bm25s.tokenize([_tokenise(query)], stopwords="en", show_progress=False),
                                      k=len(cards), show_progress=False)
    return [cards[int(i)]["passage_id"] for i, s in zip(docs[0], scores[0]) if s > 0]


def run(build: Path) -> dict:
    cfg = {**SETTINGS.raw.get("retrieval", {}), "mode": "hybrid"}
    queries = dev_queries(build)
    cards = load_cards(ROOT / cfg["cards"])
    dense_retriever, notices = build_retriever(cfg, ROOT)
    bm25_retriever = HybridRetriever(dense_retriever.cards, dense_retriever.chunks,
                                     rrf_k=dense_retriever.rrf_k, depth=dense_retriever.depth)

    def ranking(retriever, q, kinds):
        return [r["passage_id"] for r in retriever.search(q["query"], chapter=None, kinds=kinds, k=40)]

    def cards_only(ids):
        return [pid for pid in ids if pid.startswith("normalized:")]

    arms = {"cards_bm25_poc_tokenizer": [poc_bm25_ranking(cards, q["query"]) for q in queries],
            "cards_bm25": [ranking(bm25_retriever, q, ("card",)) for q in queries]}
    hybrid_bm25 = [ranking(bm25_retriever, q, ("card", "section")) for q in queries]
    arms["hybrid_bm25_rrf/strict"] = hybrid_bm25
    arms["hybrid_bm25_rrf/cards"] = [cards_only(r) for r in hybrid_bm25]
    if dense_retriever.dense:
        arms["cards_bm25+dense"] = [ranking(dense_retriever, q, ("card",)) for q in queries]
        hybrid_dense = [ranking(dense_retriever, q, ("card", "section")) for q in queries]
        arms["hybrid_bm25+dense_rrf/strict"] = hybrid_dense
        arms["hybrid_bm25+dense_rrf/cards"] = [cards_only(r) for r in hybrid_dense]
    import hashlib
    return {"run_id": f"s3_retrieval-{dt.datetime.now():%Y%m%d-%H%M%S}",
            "config": {"file": "config/app.toml", "sha256": hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest(),
                       **{k: cfg.get(k) for k in ("cards", "index_dir", "dense_model", "rrf_k", "depth")}},
            "data": "development retrieval_judgments (15 queries; labels assistant-proposed, not human)",
            "sections_indexed": len(dense_retriever.chunks), "dense": dense_retriever.dense, "notices": notices,
            "results": {name: metrics(r, queries) for name, r in arms.items()},
            "per_query": [{"query_id": q["query_id"], **{name: r[i][:5] for name, r in arms.items()}}
                          for i, q in enumerate(queries)]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Development Recall@5 and MRR for card and hybrid retrieval")
    parser.add_argument("--build", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--out", type=Path, default=ROOT / "var" / "retrieval_runs")
    args = parser.parse_args(argv)
    report = run(args.build)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{report['run_id']}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("run_id", "config", "sections_indexed", "dense", "notices", "results")},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
