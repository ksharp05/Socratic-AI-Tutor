"""Hybrid retrieval: BM25 over cards + BM25 over NCERT section chunks (+ optional dense), fused by RRF.

Each ranked list is scored over its whole collection (the collections are small), filtered by chapter
and kind, cut to `depth`, then fused with Reciprocal Rank Fusion (k = 60, Docs/plan/04-architecture.md).
Results carry `kind` ("card" or "section"), citation fields and the source page. Section text is
extracted PDF text: formulas in it are unreliable, so section results say `use_for_formulas: false`
and formulas are cited from cards (TP-T2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bm25s
import numpy as np

from .textnorm import tokenize

KINDS = ("card", "section")


def rrf(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion: score(d) = sum over lists of 1 / (k + rank). Ties keep first-seen order."""
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    order = {doc: i for i, doc in enumerate(scores)}
    return sorted(scores.items(), key=lambda kv: (-kv[1], order[kv[0]]))


class BM25Index:
    def __init__(self, texts: list[str]):
        self.size = len(texts)
        self._bm25 = None
        if texts:
            self._bm25 = bm25s.BM25()
            self._bm25.index([tokenize(t) or ["_empty_"] for t in texts], show_progress=False)

    def scores(self, query: str) -> np.ndarray:
        tokens = tokenize(query)
        if self._bm25 is None or not tokens:
            return np.zeros(self.size)
        return np.asarray(self._bm25.get_scores(tokens), dtype=float)


def card_text(card: dict) -> str:
    return f"{card['title']} {card['text']} {card.get('hint', '')} {card.get('diagnostic_probe', '')}"


def card_passage(card: dict) -> dict:
    anchor = card.get("source_anchor") or {}
    return {"passage_id": card["passage_id"], "kind": "card", "concept_id": card["concept_id"],
            "title": card["title"], "text": card["text"], "chapter": card["chapter"], "class": card["class"],
            "source": {"url": anchor.get("source_url"), "page": anchor.get("source_printed_page"),
                       "pdf_page": anchor.get("source_pdf_page"), "section": anchor.get("source_section")}}


def section_passage(chunk: dict) -> dict:
    return {"passage_id": chunk["passage_id"], "kind": "section",
            "title": f"{chunk['section']} {chunk['section_title']}", "section_kind": chunk["kind"],
            "text": chunk["text"], "chapter": chunk["chapter"], "class": chunk.get("class", 10),
            "use_for_formulas": False,
            "source": {"url": chunk.get("source_url"), "page": chunk.get("printed_page"),
                       "pdf_page": chunk.get("pdf_page"), "section": chunk["section"]}}


class HybridRetriever:
    def __init__(self, cards: list[dict], chunks: list[dict], *, encoder=None, chunk_vectors=None,
                 rrf_k: int = 60, depth: int = 20):
        self.cards, self.chunks = cards, chunks
        self.rrf_k, self.depth = rrf_k, depth
        self.docs = [card_passage(c) for c in cards] + [section_passage(c) for c in chunks]
        self.by_id = {d["passage_id"]: d for d in self.docs}
        self.card_bm25 = BM25Index([card_text(c) for c in cards])
        self.section_bm25 = BM25Index([c["text"] for c in chunks])
        self.encoder = encoder
        self.vectors = None
        if encoder is not None:
            card_vecs = encoder.embed_passages([card_text(c) for c in cards])
            if chunk_vectors is None or len(chunk_vectors) != len(chunks):
                chunk_vectors = encoder.embed_passages([c["text"] for c in chunks]) if chunks else None
            self.vectors = card_vecs if chunk_vectors is None else np.vstack([card_vecs, chunk_vectors])

    @property
    def dense(self) -> bool:
        return self.vectors is not None

    def _ranked(self, scores: np.ndarray, offset: int, allowed: set[int]) -> list[str]:
        order = np.argsort(-scores, kind="stable")
        out = []
        for i in order:
            if scores[i] <= 0:
                break
            if offset + int(i) in allowed:
                out.append(self.docs[offset + int(i)]["passage_id"])
                if len(out) == self.depth:
                    break
        return out

    def rankings(self, query: str, *, chapter: str | None = None, kinds=KINDS) -> dict[str, list[str]]:
        allowed = {i for i, d in enumerate(self.docs)
                   if d["kind"] in kinds and (not chapter or d["chapter"] == chapter)}
        lists = {}
        if "card" in kinds:
            lists["bm25_cards"] = self._ranked(self.card_bm25.scores(query), 0, allowed)
        if "section" in kinds and self.chunks:
            lists["bm25_sections"] = self._ranked(self.section_bm25.scores(query), len(self.cards), allowed)
        if self.vectors is not None:
            sims = self.vectors @ self.encoder.embed_query(query)
            sims = np.where(sims > 0, sims, 1e-9)  # cosine can be <= 0; keep every allowed doc rankable
            lists["dense"] = self._ranked(sims, 0, allowed)
        return lists

    def search(self, query: str, *, chapter: str | None = None, kinds=KINDS, k: int = 5) -> list[dict]:
        lists = self.rankings(query, chapter=chapter, kinds=kinds)
        fused = rrf(list(lists.values()), k=self.rrf_k)[:k]
        results = []
        for pid, score in fused:
            ranks = {name: ranking.index(pid) + 1 for name, ranking in lists.items() if pid in ranking}
            results.append({**self.by_id[pid], "score": round(score, 5), "ranks": ranks})
        return results

    def get(self, passage_id: str) -> dict | None:
        return self.by_id.get(passage_id)


def load_cards(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_index(index_dir: Path) -> tuple[list[dict], dict, np.ndarray | None] | None:
    chunks_path, manifest_path = index_dir / "chunks.jsonl", index_dir / "manifest.json"
    if not (chunks_path.exists() and manifest_path.exists()):
        return None
    chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dense_path = index_dir / "dense.npy"
    vectors = np.load(dense_path) if manifest.get("dense") and dense_path.exists() else None
    return chunks, manifest, vectors


def build_retriever(cfg: dict, root: Path) -> tuple[HybridRetriever, list[str]]:
    """Builds the hybrid retriever from the [retrieval] config. Returns it with any notices
    (missing index, dense off) that callers should surface."""
    cards = load_cards(root / cfg.get("cards", "content/dataset-v0.10.0/corpus.jsonl"))
    index_dir = root / cfg.get("index_dir", "data/ncert/index")
    notices: list[str] = []
    loaded = load_index(index_dir)
    chunks, vectors = [], None
    if loaded is None:
        notices.append(f"NCERT section index not found at {index_dir}; serving cards only. "
                       "Build it with `python -m tutor.retrieval.ingest`.")
    else:
        chunks, _, vectors = loaded
    encoder = None
    if cfg.get("dense", True):
        from .dense import DenseEncoder, available
        if not available():
            notices.append("dense vectors off: fastembed is not installed")
        else:
            try:
                encoder = DenseEncoder(cfg.get("dense_model", "BAAI/bge-small-en-v1.5"),
                                       root / cfg.get("model_cache", "data/models"))
            except Exception as exc:  # model not cached, or ONNX failed: BM25 still works
                notices.append(f"dense vectors off: {type(exc).__name__}: {str(exc)[:160]}")
    for notice in notices:
        print(f"textbook-kb: {notice}", file=sys.stderr)
    return HybridRetriever(cards, chunks, encoder=encoder, chunk_vectors=vectors,
                           rrf_k=int(cfg.get("rrf_k", 60)), depth=int(cfg.get("depth", 20))), notices
