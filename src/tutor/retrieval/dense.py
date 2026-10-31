"""Optional dense vectors with fastembed (ONNX, CPU only).

The model is downloaded once, at ingest time, into data/models/ (git-ignored). At query time it is
loaded with `local_files_only`, so the tutor never touches the network. If fastembed is missing or the
model is not cached, hybrid retrieval runs on BM25 alone and says so.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np


def available() -> bool:
    try:
        import fastembed  # noqa: F401
    except ImportError:
        return False
    return True


class DenseEncoder:
    def __init__(self, model: str, cache_dir: Path | None, *, allow_download: bool = False):
        from fastembed import TextEmbedding
        self.model_name = model
        self._model = TextEmbedding(model, cache_dir=str(cache_dir) if cache_dir else None,
                                    local_files_only=not allow_download)
        self.dim = int(self.embed_passages(["probe"]).shape[1])

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        return np.asarray(list(self._model.passage_embed(texts)), dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(next(iter(self._model.query_embed(text))), dtype=np.float32)
