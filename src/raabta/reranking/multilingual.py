"""Pinned CrossEncoder reranking over a small fused candidate set."""

from __future__ import annotations

import os
from pathlib import Path

from raabta.data.models import Passage
from raabta.retrieval.models import SearchResult


class MultilingualReranker:
    def __init__(
        self,
        model_name: str,
        revision: str,
        code_revision: str = "40ced75c3017eb27626c9d4ea981bde21a2662f4",
        cache_folder: str | Path = "artifacts/models/reranker",
        device: str = "cpu",
        local_files_only: bool = False,
        batch_size: int = 4,
    ) -> None:
        cache_path = Path(cache_folder).resolve()
        os.environ.setdefault("HF_HOME", str(cache_path))
        try:
            import truststore

            truststore.inject_into_ssl()
        except ImportError:
            pass
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(
            model_name,
            device=device,
            cache_dir=str(cache_path),
            trust_remote_code=True,
            revision=revision,
            automodel_args={"code_revision": code_revision},
            local_files_only=local_files_only,
            max_length=512,
        )
        self.batch_size = batch_size

    def rerank(
        self,
        query: str,
        candidates: list[SearchResult],
        passages_by_id: dict[str, Passage],
    ) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not candidates:
            return []
        pairs = [(query, passages_by_id[item.passage_id].passage_text) for item in candidates]
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        rescored = list(zip(candidates, (float(score) for score in scores), strict=True))
        rescored.sort(key=lambda item: (-item[1], item[0].passage_id))
        return [
            SearchResult(
                passage_id=candidate.passage_id,
                score=score,
                rank=rank,
                route="reranker",
                contributing_routes=tuple(
                    sorted(set(candidate.contributing_routes) | {"reranker"})
                ),
            )
            for rank, (candidate, score) in enumerate(rescored, start=1)
        ]
