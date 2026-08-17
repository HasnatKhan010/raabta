"""CPU exact dense retrieval with cached, normalized NumPy embeddings."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import numpy as np

from raabta.data.models import Passage
from raabta.retrieval.models import SearchResult


class Encoder(Protocol):
    def encode(self, texts: Sequence[str]) -> np.ndarray: ...


class E5Encoder:
    def __init__(
        self,
        model_name: str,
        revision: str,
        device: str = "cpu",
        cache_folder: str | Path = "artifacts/models/huggingface",
        local_files_only: bool = False,
    ) -> None:
        cache_path = Path(cache_folder).resolve()
        os.environ.setdefault("HF_HOME", str(cache_path))
        try:
            import truststore

            truststore.inject_into_ssl()
        except ImportError:
            pass
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(
            model_name,
            revision=revision,
            device=device,
            cache_folder=str(cache_path),
            local_files_only=local_files_only,
        )

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        return np.asarray(
            self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32,
        )


def normalize_rows(values: np.ndarray) -> np.ndarray:
    matrix = np.asarray(values, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.maximum(norms, np.finfo(np.float32).eps)


class DenseRetriever:
    def __init__(self, passages: list[Passage], embeddings: np.ndarray, encoder: Encoder) -> None:
        if len(passages) != len(embeddings) or not passages:
            raise ValueError("passages and embeddings must be non-empty and aligned")
        self.passages = passages
        self.embeddings = normalize_rows(embeddings)
        self.encoder = encoder

    def search(self, query: str, top_k: int = 10, route: str = "dense") -> list[SearchResult]:
        if not query.strip():
            raise ValueError("query must not be empty")
        query_vector = normalize_rows(self.encoder.encode([f"query: {query}"]))[0]
        scores = self.embeddings @ query_vector
        indices = sorted(range(len(scores)), key=lambda index: (-scores[index], index))[:top_k]
        return [
            SearchResult(self.passages[index].passage_id, float(scores[index]), rank, route)
            for rank, index in enumerate(indices, start=1)
        ]


def encode_passages(passages: list[Passage], encoder: Encoder, batch_size: int = 32) -> np.ndarray:
    batches: list[np.ndarray] = []
    for start in range(0, len(passages), batch_size):
        texts = [f"passage: {item.passage_text}" for item in passages[start : start + batch_size]]
        batches.append(encoder.encode(texts))
    return normalize_rows(np.vstack(batches))
