from __future__ import annotations

import unittest

import numpy as np

from raabta.data.models import Passage
from raabta.reranking.multilingual import MultilingualReranker
from raabta.retrieval.models import SearchResult


class FakeCrossEncoder:
    def predict(self, pairs, **kwargs):
        return np.asarray([0.2, 0.9], dtype=np.float32)


class RerankingTests(unittest.TestCase):
    def test_reranker_reorders_and_preserves_trace(self) -> None:
        reranker = object.__new__(MultilingualReranker)
        reranker.model = FakeCrossEncoder()
        reranker.batch_size = 2
        passages = {
            "p1": Passage("p1", "a", "one", "url", "general", 0, "first", 1),
            "p2": Passage("p2", "a", "two", "url", "general", 1, "second", 1),
        }
        candidates = [
            SearchResult("p1", 1.0, 1, "rrf", ("dense",)),
            SearchResult("p2", 0.5, 2, "rrf", ("bm25",)),
        ]
        output = reranker.rerank("query", candidates, passages)
        self.assertEqual(output[0].passage_id, "p2")
        self.assertIn("reranker", output[0].contributing_routes)


if __name__ == "__main__":
    unittest.main()
