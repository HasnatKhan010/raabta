from __future__ import annotations

import unittest

from raabta.evaluation.metrics import ndcg_at_k, recall_at_k, reciprocal_rank


class MetricTests(unittest.TestCase):
    def test_reciprocal_rank(self) -> None:
        self.assertEqual(reciprocal_rank(["x", "gold"], {"gold"}), 0.5)

    def test_recall(self) -> None:
        self.assertEqual(recall_at_k(["a", "b"], {"a", "c"}, 2), 0.5)

    def test_ndcg_is_one_for_ideal_rank(self) -> None:
        self.assertEqual(ndcg_at_k(["gold", "x"], {"gold"}), 1.0)


if __name__ == "__main__":
    unittest.main()
