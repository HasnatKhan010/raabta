"""Multi-query, multi-route retrieval with transparent RRF."""

from __future__ import annotations

from dataclasses import dataclass

from raabta.querybridge.bridge import QueryBridge, QueryVariant
from raabta.retrieval.dense import DenseRetriever
from raabta.retrieval.fusion import reciprocal_rank_fusion
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.models import SearchResult
from raabta.retrieval.roman_title import RomanizedTitleRetriever


@dataclass(frozen=True, slots=True)
class MultiQueryOutput:
    variants: tuple[QueryVariant, ...]
    results: tuple[SearchResult, ...]
    route_sizes: dict[str, int]


class MultiQueryRetriever:
    def __init__(
        self,
        bridge: QueryBridge,
        bm25: BM25Retriever,
        dense: DenseRetriever,
        roman_title: RomanizedTitleRetriever | None = None,
        fusion_constant: int = 60,
    ) -> None:
        self.bridge = bridge
        self.bm25 = bm25
        self.dense = dense
        self.roman_title = roman_title
        self.fusion_constant = fusion_constant

    @staticmethod
    def _route_weight(route: str) -> float:
        """Prefer Urdu lexical agreement without discarding cross-script evidence."""
        retriever, _, variant_type = route.partition(":")
        variant_type = variant_type.rsplit(":", maxsplit=1)[-1]
        if retriever == "roman_title":
            return 3.0
        if retriever == "bm25":
            return {
                "original": 0.55,
                "normalized_roman": 0.65,
                "urdu_script": 1.35,
                "retrieval_oriented": 1.05,
            }.get(variant_type, 1.0)
        return {
            "original": 1.0,
            "normalized_roman": 0.9,
            "urdu_script": 1.2,
            "retrieval_oriented": 0.95,
        }.get(variant_type, 1.0)

    def search(
        self,
        query: str,
        route_top_k: int = 20,
        final_top_k: int = 10,
        *,
        use_normalization: bool = True,
        use_transliteration: bool = True,
        use_expansion: bool = True,
        use_bm25: bool = True,
        use_dense: bool = True,
        use_roman_title: bool = True,
        use_fusion: bool = True,
    ) -> MultiQueryOutput:
        if not use_bm25 and not use_dense:
            raise ValueError("at least one retrieval route must be enabled")
        default_generation = use_normalization and use_transliteration and use_expansion
        if default_generation and not hasattr(self.bridge, "generate_configured"):
            variants = self.bridge.generate(query)
        else:
            variants = self.bridge.generate_configured(
                query,
                use_normalization=use_normalization,
                use_transliteration=use_transliteration,
                use_expansion=use_expansion,
            )
        routes: dict[str, list[SearchResult]] = {}
        if use_roman_title and self.roman_title is not None:
            title_route = "roman_title:original"
            title_results = self.roman_title.search(query, route_top_k, route=title_route)
            if title_results:
                routes[title_route] = title_results
        for variant in variants:
            if not variant.accepted:
                continue
            bm25_route = f"bm25:{variant.variant_id}:{variant.variant_type}"
            dense_route = f"dense:{variant.variant_id}:{variant.variant_type}"
            if use_bm25:
                lexical = self.bm25.search(variant.query_text, route_top_k, route=bm25_route)
                if lexical:
                    routes[bm25_route] = lexical
            if use_dense:
                routes[dense_route] = self.dense.search(
                    variant.query_text, route_top_k, route=dense_route
                )
        if use_fusion:
            weights = {route: self._route_weight(route) for route in routes}
            final = reciprocal_rank_fusion(
                routes,
                constant=self.fusion_constant,
                weights=weights,
                top_k=final_top_k,
            )
        else:
            # A deterministic no-fusion control: preserve route insertion order and
            # append unseen passages without combining incomparable score scales.
            final = []
            seen: set[str] = set()
            for route_results in routes.values():
                for result in route_results:
                    if result.passage_id not in seen:
                        final.append(result)
                        seen.add(result.passage_id)
                    if len(final) == final_top_k:
                        break
                if len(final) == final_top_k:
                    break
            final = [
                SearchResult(
                    passage_id=result.passage_id,
                    score=result.score,
                    rank=rank,
                    route="fixed_route_concatenation",
                    contributing_routes=(result.route,),
                )
                for rank, result in enumerate(final, start=1)
            ]
        return MultiQueryOutput(
            variants=tuple(variants),
            results=tuple(final),
            route_sizes={route: len(results) for route, results in routes.items()},
        )
