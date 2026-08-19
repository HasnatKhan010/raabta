from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.evidence.curated import curated_answer_for
from raabta.evidence.extractive import ExtractiveAnswerer, GroundedAnswer
from raabta.evidence.relevance import (
    content_token_overlap,
    is_definition_query,
    reranker_confidence,
    validate_answer_shape,
)
from raabta.querybridge.bridge import QueryBridge, QueryVariant, SupportingLexiconTransliterator
from raabta.querybridge.transliteration import single_transliteration
from raabta.reranking.multilingual import MultilingualReranker
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.fusion import reciprocal_rank_fusion
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.models import SearchResult
from raabta.retrieval.multiquery import MultiQueryRetriever
from raabta.retrieval.roman_title import RomanizedTitleRetriever
from raabta.retrieval.wikipedia import UrduWikipediaClient


class RaabtaEngine:
    minimum_reranker_score = 0.62

    def __init__(self, root: Path, *, wikipedia: UrduWikipediaClient | None = None) -> None:
        self.root = root.resolve()
        passage_path = self.root / "data/processed/passages_150_30.jsonl"
        embedding_path = self.root / "artifacts/embeddings/e5_small_150_30.npy"
        lexicon_path = self.root / "artifacts/metadata/transliteration_lexicon.json"
        self.passages = [Passage(**row) for row in read_jsonl(passage_path)]
        self.passages_by_id = {item.passage_id: item for item in self.passages}
        embeddings = np.load(embedding_path, allow_pickle=False, mmap_mode="r")
        self.encoder = E5Encoder(
            "intfloat/multilingual-e5-small",
            "d1d99a1efae6779390caba937d92c54b5bc70e51",
            local_files_only=True,
        )
        self.bm25 = BM25Retriever(self.passages, title_boost=3)
        self.dense = DenseRetriever(self.passages, embeddings, self.encoder)
        self.bridge = QueryBridge(SupportingLexiconTransliterator(lexicon_path), self.encoder, 0.55)
        self.roman_title = RomanizedTitleRetriever(self.passages)
        self.multiquery = MultiQueryRetriever(
            self.bridge, self.bm25, self.dense, roman_title=self.roman_title
        )
        self.reranker = MultilingualReranker(
            "Alibaba-NLP/gte-multilingual-reranker-base",
            "a6258e9d2b1a11aa7bccdff9efde562bbca4393d",
            local_files_only=True,
        )
        self.answerer = ExtractiveAnswerer(
            self.encoder,
            similarity_threshold=0.70,
            candidate_depth=1,
            max_sentences=1,
        )
        self.wikipedia = wikipedia or UrduWikipediaClient()

    @staticmethod
    def _rank(results, gold: str | None) -> int | None:
        if gold is None:
            return None
        return next((item.rank for item in results if item.passage_id == gold), None)

    @staticmethod
    def _reranker_query(query: str, variants: tuple[QueryVariant, ...]) -> str:
        urdu = next(
            (
                item
                for item in variants
                if item.accepted
                and item.variant_type == "urdu_script"
                and item.transliteration_coverage >= 0.55
            ),
            None,
        )
        return query if urdu is None else urdu.query_text

    def _trace(self, results: list[SearchResult] | tuple[SearchResult, ...]) -> list[dict]:
        trace: list[dict] = []
        for item in results:
            passage = self.passages_by_id.get(item.passage_id)
            payload = asdict(item)
            if passage is not None:
                payload.update(
                    {
                        "title": passage.title,
                        "url": passage.url,
                        "snippet": passage.passage_text[:260].strip(),
                        "domain": passage.domain,
                    }
                )
            payload["score_type"] = (
                "cross_encoder_relevance" if item.route == "reranker" else "fusion_rank_score"
            )
            trace.append(payload)
        return trace

    def _answer_candidates(
        self,
        query: str,
        reranker_query: str,
        candidates: list[SearchResult],
    ) -> tuple[GroundedAnswer, list[str], dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        diagnostics: dict[str, Any] = {"validation_checks": checks}
        if not candidates:
            checks.append(
                {
                    "id": "candidate",
                    "label": "Candidate evidence",
                    "status": "failed",
                    "detail": "No passages were retrieved.",
                }
            )
            diagnostics.update(
                {"top_relevance_score": 0.0, "confidence": "low", "content_overlap": 0.0}
            )
            return (
                self.answerer.abstain(query, "no_retrieved_evidence"),
                ["No candidate passages were retrieved."],
                diagnostics,
            )
        top_score = float(candidates[0].score)
        second_score = float(candidates[1].score) if len(candidates) > 1 else None
        confidence = reranker_confidence(top_score, second_score)
        diagnostics.update(
            {
                "top_relevance_score": round(top_score, 6),
                "second_relevance_score": round(second_score or 0.0, 6),
                "confidence": confidence,
            }
        )
        checks.append(
            {
                "id": "relevance",
                "label": "Reranker relevance",
                "status": "passed" if top_score >= self.minimum_reranker_score else "failed",
                "value": round(top_score, 6),
                "threshold": self.minimum_reranker_score,
                "detail": "Cross-encoder relevance must clear the safety threshold.",
            }
        )
        if top_score < self.minimum_reranker_score:
            return (
                self.answerer.abstain(
                    query,
                    f"weak_reranker_relevance:{top_score:.6f}<{self.minimum_reranker_score:.6f}",
                ),
                [
                    "The best passage did not pass the relevance threshold.",
                    "Raabta rejected it instead of showing a likely unrelated answer.",
                ],
                diagnostics,
            )

        top_passage = self.passages_by_id[candidates[0].passage_id]
        overlap_count, overlap_ratio = content_token_overlap(
            reranker_query, f"{top_passage.title} {top_passage.passage_text}"
        )
        title_similarity = self.roman_title.similarity(query, top_passage.passage_id)
        title_route_contributed = "roman_title:original" in candidates[0].contributing_routes
        cross_script_title_match = title_route_contributed and title_similarity >= 0.30
        diagnostics["content_overlap"] = round(overlap_ratio, 6)
        diagnostics["content_overlap_count"] = overlap_count
        diagnostics["title_match_score"] = round(title_similarity, 6)
        checks.append(
            {
                "id": "overlap",
                "label": "Query-to-source alignment",
                "status": "passed" if overlap_count > 0 or cross_script_title_match else "failed",
                "value": (
                    round(overlap_ratio, 6) if overlap_count > 0 else round(title_similarity, 6)
                ),
                "threshold": (
                    "> 0 converted terms" if overlap_count > 0 else "0.30 title similarity"
                ),
                "detail": (
                    f"{overlap_count} meaningful converted terms overlap the source; "
                    f"Romanized title similarity is {title_similarity:.3f}."
                ),
            }
        )
        if overlap_count == 0 and not cross_script_title_match:
            return (
                self.answerer.abstain(query, "no_query_content_overlap"),
                [
                    "The top passage shared no meaningful query term after script conversion.",
                    "Raabta rejected the semantic match as unsafe.",
                ],
                diagnostics,
            )

        answer = self.answerer.answer(
            query,
            candidates[:1],
            self.passages_by_id,
            evidence_queries=[reranker_query, query],
            sentence_validator=lambda sentence: validate_answer_shape(query, sentence).accepted,
            prefer_lead=is_definition_query(query),
        )
        if not answer.supported:
            checks.append(
                {
                    "id": "evidence",
                    "label": "Evidence sentence similarity",
                    "status": "failed",
                    "threshold": self.answerer.similarity_threshold,
                    "detail": answer.abstention_reason,
                }
            )
            return answer, ["No sentence passed the evidence-similarity threshold."], diagnostics
        best_similarity = max(item.similarity for item in answer.evidence)
        checks.append(
            {
                "id": "evidence",
                "label": "Evidence sentence similarity",
                "status": "passed",
                "value": best_similarity,
                "threshold": self.answerer.similarity_threshold,
                "detail": "The selected sentence is semantically aligned with the question.",
            }
        )
        shape = validate_answer_shape(query, answer.answer)
        diagnostics["query_intent"] = shape.intent
        diagnostics["answer_type_check"] = shape.reason
        checks.append(
            {
                "id": "answer_type",
                "label": f"Requested answer type: {shape.intent}",
                "status": "passed" if shape.accepted else "failed",
                "detail": shape.reason,
            }
        )
        if not shape.accepted:
            return (
                self.answerer.abstain(query, shape.reason),
                [
                    "A topical passage was found, but it did not contain the kind of fact requested.",
                    f"Validation check: {shape.reason}.",
                ],
                diagnostics,
            )
        return (
            answer,
            [
                "The top passage passed reranker, content-overlap, and answer-type checks.",
                "The displayed answer is copied directly from the cited evidence.",
            ],
            diagnostics,
        )

    def _live_candidates(self, reranker_query: str) -> tuple[list[SearchResult], str | None, float]:
        started = time.perf_counter()
        live = self.wikipedia.search(reranker_query)
        if not live.passages:
            return [], live.error, (time.perf_counter() - started) * 1000
        for passage in live.passages:
            self.passages_by_id[passage.passage_id] = passage
        initial = [
            SearchResult(
                passage_id=passage.passage_id,
                score=1.0 / rank,
                rank=rank,
                route="live_wikipedia_search",
                contributing_routes=("live_wikipedia_search",),
            )
            for rank, passage in enumerate(live.passages[:10], start=1)
        ]
        reranked = self.reranker.rerank(reranker_query, initial, self.passages_by_id)
        return reranked, live.error, (time.perf_counter() - started) * 1000

    def compare(self, query: str, gold_passage_id: str | None = None) -> dict:
        dense = self.dense.search(query, top_k=10)
        single = self.bm25.search(single_transliteration(query), top_k=10)
        raw_bm25 = self.bm25.search(query, top_k=20)
        hybrid = reciprocal_rank_fusion({"bm25": raw_bm25, "dense": dense}, top_k=10)
        raabta = self.multiquery.search(query, route_top_k=20, final_top_k=10).results
        systems = {
            "direct_dense": dense,
            "single_transliteration_bm25": single,
            "standard_hybrid": hybrid,
            "raabta_no_reranker": raabta,
        }
        return {
            name: {
                "gold_rank": self._rank(results, gold_passage_id),
                "gold_status": "NOT PROVIDED"
                if gold_passage_id is None
                else "NOT RETRIEVED"
                if self._rank(results, gold_passage_id) is None
                else "RETRIEVED",
                "passage_ids": [item.passage_id for item in results],
            }
            for name, results in systems.items()
        }

    def query(self, query: str, research_mode: bool = False, live_search: bool = False) -> dict:
        total_started = time.perf_counter()
        curated = curated_answer_for(query)
        if curated is not None:
            elapsed_ms = (time.perf_counter() - total_started) * 1000
            evidence = {
                "passage_id": curated.passage_id,
                "article_id": "curated-facts",
                "title": curated.title,
                "url": curated.url,
                "sentence_index": 0,
                "text": curated.answer,
                "similarity": 1.0,
                "retrieval_rank": 0,
            }
            return {
                "query": query,
                "supported": True,
                "answer": curated.answer,
                "query_variants": [],
                "evidence": [evidence],
                "sources": [{"title": curated.title, "url": curated.url}],
                "retrieval_trace": [],
                "scores": {"best_evidence_similarity": 1.0, "top_reranker_score": 1.0},
                "latency_ms": {
                    "retrieval": 0.0,
                    "hybrid_retrieval": 0.0,
                    "reranking": 0.0,
                    "live_search": 0.0,
                    "answer_selection": round(elapsed_ms, 3),
                    "total": round(elapsed_ms, 3),
                },
                "abstention_reason": None,
                "pipeline": {
                    "mode": "curated_fact_card",
                    "decision": "answer",
                    "confidence": "high",
                    "reranker_query": None,
                    "local_candidate_count": 0,
                    "live_candidate_count": 0,
                    "live_search_requested": live_search,
                    "reasons": ["Matched a narrowly defined, explicitly sourced fact card."],
                    "accepted_variant_count": 0,
                    "route_candidate_counts": {},
                    "validation_checks": [
                        {
                            "id": "curated_fact",
                            "label": "Verified fact card",
                            "status": "passed",
                            "value": 1.0,
                            "threshold": 1.0,
                            "detail": "An exact, explicitly sourced fact card matched the question.",
                        }
                    ],
                    "stages": [
                        {
                            "id": "fact_card",
                            "label": "Exact fact-card match",
                            "status": "passed",
                            "detail": "Retrieval was bypassed because a verified exact match was available.",
                        }
                    ],
                    "corpus_notice": "This answer used an explicit fact card, not free-form generation.",
                },
                "research_comparison": self.compare(query) if research_mode else None,
            }

        retrieval_started = time.perf_counter()
        retrieval = self.multiquery.search(query, route_top_k=30, final_top_k=20)
        hybrid_ms = (time.perf_counter() - retrieval_started) * 1000
        reranker_query = self._reranker_query(query, retrieval.variants)

        rerank_started = time.perf_counter()
        local_reranked = self.reranker.rerank(
            reranker_query, list(retrieval.results), self.passages_by_id
        )
        rerank_ms = (time.perf_counter() - rerank_started) * 1000
        answer_started = time.perf_counter()
        answer, reasons, diagnostics = self._answer_candidates(
            query, reranker_query, local_reranked
        )
        local_supported = answer.supported
        local_abstention_reason = answer.abstention_reason
        mode = "local_corpus"
        chosen_results = local_reranked
        live_ms = 0.0
        live_error: str | None = None
        live_count = 0

        if not answer.supported and live_search:
            live_results, live_error, live_ms = self._live_candidates(reranker_query)
            live_count = len(live_results)
            if live_results:
                live_answer, live_reasons, live_diagnostics = self._answer_candidates(
                    query, reranker_query, live_results
                )
                if live_answer.supported:
                    answer = live_answer
                    reasons = [
                        "The bounded local corpus did not produce reliable evidence.",
                        "The user-enabled live Urdu Wikipedia fallback supplied replacement evidence.",
                        *live_reasons,
                    ]
                    diagnostics = live_diagnostics
                    chosen_results = live_results
                    mode = "live_wikipedia"
                else:
                    reasons = [
                        *reasons,
                        "The user-enabled live fallback was checked but also failed validation.",
                    ]

        answer_ms = max(0.0, (time.perf_counter() - answer_started) * 1000 - live_ms)
        evidence_similarity = max((item.similarity for item in answer.evidence), default=0.0)
        sources = (
            []
            if not answer.supported
            else [{"title": answer.source_title, "url": answer.source_url}]
        )
        total_ms = (time.perf_counter() - total_started) * 1000
        pipeline = {
            "mode": mode if answer.supported else "abstained",
            "decision": "answer" if answer.supported else "abstain",
            "confidence": diagnostics.get("confidence", "low"),
            "reranker_query": reranker_query,
            "local_candidate_count": len(local_reranked),
            "live_candidate_count": live_count,
            "live_search_requested": live_search,
            "live_search_error": live_error,
            "top_relevance_score": diagnostics.get("top_relevance_score", 0.0),
            "content_overlap": diagnostics.get("content_overlap", 0.0),
            "title_match_score": diagnostics.get("title_match_score", 0.0),
            "query_intent": diagnostics.get("query_intent", "general"),
            "reasons": reasons,
            "accepted_variant_count": sum(item.accepted for item in retrieval.variants),
            "route_candidate_counts": retrieval.route_sizes,
            "validation_checks": diagnostics.get("validation_checks", []),
            "stages": [
                {
                    "id": "query_bridge",
                    "label": "Normalize and convert the query",
                    "status": "passed",
                    "detail": (
                        f"Accepted {sum(item.accepted for item in retrieval.variants)} of "
                        f"{len(retrieval.variants)} traceable query forms."
                    ),
                },
                {
                    "id": "roman_title",
                    "label": "Match noisy Roman text to Urdu titles",
                    "status": (
                        "passed"
                        if retrieval.route_sizes.get("roman_title:original", 0)
                        else "no_match"
                    ),
                    "detail": (
                        f"Found {retrieval.route_sizes.get('roman_title:original', 0)} "
                        "title candidates using character-level matching."
                    ),
                },
                {
                    "id": "hybrid_retrieval",
                    "label": "Search lexical and semantic routes",
                    "status": "passed" if local_reranked else "failed",
                    "detail": (
                        f"Combined {len(retrieval.route_sizes)} active routes into "
                        f"{len(local_reranked)} local candidates."
                    ),
                },
                {
                    "id": "reranking",
                    "label": "Rerank candidates with the multilingual model",
                    "status": "passed" if local_reranked else "failed",
                    "detail": (
                        f"Scored the top {len(local_reranked)} candidates using title plus passage text."
                    ),
                },
                {
                    "id": "local_validation",
                    "label": "Validate local evidence",
                    "status": "passed" if local_supported else "failed",
                    "detail": (
                        "The local evidence passed every gate."
                        if local_supported
                        else f"Local evidence was rejected safely: {local_abstention_reason}."
                    ),
                },
                *(
                    [
                        {
                            "id": "live_search",
                            "label": "Check live Urdu Wikipedia fallback",
                            "status": (
                                "passed"
                                if mode == "live_wikipedia" and answer.supported
                                else "failed"
                                if live_error or live_count
                                else "no_match"
                            ),
                            "detail": (
                                f"Checked {live_count} live candidates."
                                + (f" Provider error: {live_error}." if live_error else "")
                            ),
                        }
                    ]
                    if live_search
                    else []
                ),
                {
                    "id": "decision",
                    "label": "Return a grounded answer or abstain",
                    "status": "passed" if answer.supported else "failed",
                    "detail": (
                        f"Returned evidence from {mode.replace('_', ' ')}."
                        if answer.supported
                        else f"No source passed every gate: {answer.abstention_reason}."
                    ),
                },
            ],
            "corpus_notice": (
                "Local mode searches a bounded 4,000-article Urdu Wikipedia corpus. "
                "Live fallback is used only when the user explicitly enables it."
            ),
        }
        return {
            "query": query,
            "supported": answer.supported,
            "answer": answer.answer,
            "query_variants": [asdict(item) for item in retrieval.variants],
            "evidence": [asdict(item) for item in answer.evidence],
            "sources": sources,
            "retrieval_trace": self._trace(chosen_results),
            "scores": {
                "best_evidence_similarity": evidence_similarity,
                "top_reranker_score": float(diagnostics.get("top_relevance_score", 0.0)),
                "content_overlap": float(diagnostics.get("content_overlap", 0.0)),
            },
            "latency_ms": {
                "retrieval": round(hybrid_ms + rerank_ms + live_ms, 3),
                "hybrid_retrieval": round(hybrid_ms, 3),
                "reranking": round(rerank_ms, 3),
                "live_search": round(live_ms, 3),
                "answer_selection": round(answer_ms, 3),
                "total": round(total_ms, 3),
            },
            "abstention_reason": answer.abstention_reason,
            "pipeline": pipeline,
            "research_comparison": self.compare(query) if research_mode else None,
        }

    def source(self, passage_id: str) -> dict | None:
        passage = self.passages_by_id.get(passage_id)
        return None if passage is None else asdict(passage)
