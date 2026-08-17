from __future__ import annotations

import unittest

import numpy as np

from raabta.data.models import Passage
from raabta.querybridge.bridge import QueryVariant
from raabta.querybridge.transliteration import single_transliteration
from raabta.retrieval.dense import DenseRetriever
from raabta.retrieval.fusion import reciprocal_rank_fusion
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.models import SearchResult
from raabta.retrieval.multiquery import MultiQueryRetriever


def passage(identifier: str, text: str) -> Passage:
    return Passage(
        identifier,
        "article",
        identifier,
        "https://example.invalid",
        "general",
        0,
        text,
        len(text.split()),
    )


class FakeEncoder:
    def encode(self, texts):
        vectors = []
        for text in texts:
            vectors.append([1.0, 0.0] if "اسلام" in text else [0.0, 1.0])
        return np.asarray(vectors, dtype=np.float32)


class RetrievalTests(unittest.TestCase):
    def test_bm25_retrieves_lexical_match(self) -> None:
        items = [passage("p1", "اسلام آباد پاکستان کا شہر ہے"), passage("p2", "اردو ادب")]
        results = BM25Retriever(items).search("اسلام آباد", top_k=1)
        self.assertEqual(results[0].passage_id, "p1")

    def test_bm25_does_not_rank_zero_score_documents(self) -> None:
        items = [passage("p1", "اسلام آباد"), passage("p2", "اردو ادب")]
        self.assertEqual(BM25Retriever(items).search("unmatched roman tokens"), [])

    def test_dense_retrieval_uses_aligned_embeddings(self) -> None:
        items = [passage("p1", "اسلام آباد"), passage("p2", "ادب")]
        results = DenseRetriever(items, np.eye(2, dtype=np.float32), FakeEncoder()).search("اسلام")
        self.assertEqual(results[0].passage_id, "p1")

    def test_rrf_rewards_route_agreement(self) -> None:
        routes = {
            "bm25": [
                SearchResult("shared", 2.0, 2, "bm25"),
                SearchResult("only-a", 1.0, 1, "bm25"),
            ],
            "dense": [
                SearchResult("shared", 0.8, 2, "dense"),
                SearchResult("only-b", 0.9, 1, "dense"),
            ],
        }
        fused = reciprocal_rank_fusion(routes)
        self.assertEqual(fused[0].passage_id, "shared")
        self.assertEqual(fused[0].contributing_routes, ("bm25", "dense"))

    def test_one_best_transliteration_is_deterministic(self) -> None:
        self.assertEqual(
            single_transliteration("pakistan ka capital kya hy?"), "پاکستان کا دارالحکومت کیا ہے ?"
        )

    def test_multiquery_output_retains_route_trace(self) -> None:
        variant = QueryVariant(
            "v1", "original", "query", "identity", "query", True, 1.0, "accepted_original"
        )

        class Bridge:
            def generate(self, query):
                return [variant]

        class Retriever:
            def __init__(self, passage_id):
                self.passage_id = passage_id

            def search(self, query, top_k, route):
                return [SearchResult(self.passage_id, 1.0, 1, route)]

        output = MultiQueryRetriever(Bridge(), Retriever("lexical"), Retriever("semantic")).search(
            "query"
        )
        self.assertEqual(len(output.route_sizes), 2)
        self.assertEqual({result.passage_id for result in output.results}, {"lexical", "semantic"})


if __name__ == "__main__":
    unittest.main()
