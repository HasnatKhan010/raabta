from __future__ import annotations

import unittest

from raabta.data.models import Article
from raabta.data.verification import find_literal_matches
from raabta.preprocessing.chunking import chunk_article
from raabta.preprocessing.text import normalize_urdu_text


class PhaseOneAcceptanceTests(unittest.TestCase):
    def test_known_urdu_evidence_survives_pipeline(self) -> None:
        raw = "آزمائشی متن۔ اسلام آباد پاکستان کا دارالحکومت ہے۔ مزید عبارت۔"
        article = Article(
            article_id="fixture",
            title="آزمائش",
            url="https://example.invalid/fixture",
            raw_text=raw,
            clean_text=normalize_urdu_text(raw),
            domain="pakistan",
        )
        passages = chunk_article(article, chunk_size=20, overlap=4)
        matches = find_literal_matches(passages, "اسلام آباد")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].article_id, "fixture")

    def test_empty_query_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            find_literal_matches([], "   ")


if __name__ == "__main__":
    unittest.main()
