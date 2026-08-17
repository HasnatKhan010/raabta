from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.evidence.curated import curated_answer_for
from raabta.evidence.extractive import ExtractiveAnswerer
from raabta.querybridge.bridge import QueryBridge, SupportingLexiconTransliterator
from raabta.querybridge.transliteration import single_transliteration
from raabta.reranking.multilingual import MultilingualReranker
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.fusion import reciprocal_rank_fusion
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.multiquery import MultiQueryRetriever


class RaabtaEngine:
    def __init__(self, root: Path) -> None:
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
        self.bm25 = BM25Retriever(self.passages)
        self.dense = DenseRetriever(self.passages, embeddings, self.encoder)
        self.bridge = QueryBridge(SupportingLexiconTransliterator(lexicon_path), self.encoder, 0.55)
        self.multiquery = MultiQueryRetriever(self.bridge, self.bm25, self.dense)
        self.reranker = MultilingualReranker(
            "Alibaba-NLP/gte-multilingual-reranker-base",
            "a6258e9d2b1a11aa7bccdff9efde562bbca4393d",
            local_files_only=True,
        )
        self.answerer = ExtractiveAnswerer(self.encoder, similarity_threshold=0.70)

    @staticmethod
    def _rank(results, gold: str | None) -> int | None:
        if gold is None:
            return None
        return next((item.rank for item in results if item.passage_id == gold), None)

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

    def query(self, query: str, research_mode: bool = False) -> dict:
        started = time.perf_counter()
        curated = curated_answer_for(query)
        if curated is not None:
            elapsed_ms = (time.perf_counter() - started) * 1000
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
                "scores": {"best_evidence_similarity": 1.0},
                "latency_ms": {
                    "retrieval": 0.0,
                    "answer_selection": round(elapsed_ms, 3),
                    "total": round(elapsed_ms, 3),
                },
                "abstention_reason": None,
                "research_comparison": self.compare(query) if research_mode else None,
            }

        retrieval = self.multiquery.search(query, route_top_k=20, final_top_k=10)
        reranked_results = self.reranker.rerank(
            query, list(retrieval.results), self.passages_by_id
        )
        retrieval_ms = (time.perf_counter() - started) * 1000
        started = time.perf_counter()
        urdu_variants = [item.query_text for item in retrieval.variants if item.accepted and item.variant_type in ("urdu_script", "retrieval_oriented")]
        answer = self.answerer.answer(
            query,
            reranked_results,
            self.passages_by_id,
            evidence_queries=urdu_variants or [query],
        )
        answer_ms = (time.perf_counter() - started) * 1000
        sources = (
            []
            if not answer.supported
            else [{"title": answer.source_title, "url": answer.source_url}]
        )
        return {
            "query": query,
            "supported": answer.supported,
            "answer": answer.answer,
            "query_variants": [asdict(item) for item in retrieval.variants],
            "evidence": [asdict(item) for item in answer.evidence],
            "sources": sources,
            "retrieval_trace": [asdict(item) for item in reranked_results],
            "scores": {
                "best_evidence_similarity": max(
                    (item.similarity for item in answer.evidence), default=0.0
                )
            },
            "latency_ms": {
                "retrieval": round(retrieval_ms, 3),
                "answer_selection": round(answer_ms, 3),
                "total": round(retrieval_ms + answer_ms, 3),
            },
            "abstention_reason": answer.abstention_reason,
            "research_comparison": self.compare(query) if research_mode else None,
        }

    def source(self, passage_id: str) -> dict | None:
        passage = self.passages_by_id.get(passage_id)
        return None if passage is None else asdict(passage)
