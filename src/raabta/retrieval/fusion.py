"""Reciprocal Rank Fusion for incomparable retrieval score scales."""

from __future__ import annotations

from collections import defaultdict

from raabta.retrieval.models import SearchResult


def reciprocal_rank_fusion(
    routes: dict[str, list[SearchResult]],
    constant: int = 60,
    weights: dict[str, float] | None = None,
    top_k: int | None = None,
) -> list[SearchResult]:
    if constant <= 0:
        raise ValueError("constant must be positive")
    scores: dict[str, float] = defaultdict(float)
    contributors: dict[str, set[str]] = defaultdict(set)
    for route, results in routes.items():
        weight = 1.0 if weights is None else weights.get(route, 1.0)
        for result in results:
            scores[result.passage_id] += weight / (constant + result.rank)
            contributors[result.passage_id].add(route)
    ranked = sorted(scores, key=lambda item: (-scores[item], item))
    if top_k is not None:
        ranked = ranked[:top_k]
    return [
        SearchResult(
            passage_id=passage_id,
            score=scores[passage_id],
            rank=rank,
            route="rrf",
            contributing_routes=tuple(sorted(contributors[passage_id])),
        )
        for rank, passage_id in enumerate(ranked, start=1)
    ]
