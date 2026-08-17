from __future__ import annotations

import unittest

from raabta.data.models import Article
from raabta.preprocessing.chunking import chunk_article


class ChunkingTests(unittest.TestCase):
    def setUp(self) -> None:
        text = " ".join(f"لفظ{index}" for index in range(10))
        self.article = Article("a1", "عنوان", "https://example.invalid/a1", text, text, "general")

    def test_overlap_and_metadata_are_preserved(self) -> None:
        passages = chunk_article(self.article, chunk_size=6, overlap=2)
        self.assertEqual(len(passages), 2)
        self.assertEqual(
            passages[0].passage_text.split()[-2:], passages[1].passage_text.split()[:2]
        )
        self.assertEqual(passages[0].article_id, "a1")
        self.assertEqual(passages[0].url, "https://example.invalid/a1")

    def test_ids_are_deterministic(self) -> None:
        first = chunk_article(self.article, 6, 2)
        second = chunk_article(self.article, 6, 2)
        self.assertEqual([item.passage_id for item in first], [item.passage_id for item in second])

    def test_invalid_overlap_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            chunk_article(self.article, chunk_size=5, overlap=5)


if __name__ == "__main__":
    unittest.main()
