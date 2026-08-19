from __future__ import annotations

import unittest

import numpy as np

from raabta.data.models import Passage
from raabta.evidence.extractive import ExtractiveAnswerer, split_sentences
from raabta.retrieval.models import SearchResult


class FixedEncoder:
    def encode(self, texts):
        vectors = []
        for text in texts:
            vectors.append(
                [1.0, 0.0] if "اسلام آباد" in text or text.startswith("query:") else [0.0, 1.0]
            )
        return np.asarray(vectors, dtype=np.float32)


class OrthogonalEncoder:
    def encode(self, texts):
        return np.asarray(
            [[1.0, 0.0] if text.startswith("query:") else [0.0, 1.0] for text in texts],
            dtype=np.float32,
        )


def passage() -> Passage:
    return Passage(
        passage_id="p1",
        article_id="a1",
        title="پاکستان",
        url="https://example.test/a1",
        domain="pakistan",
        passage_index=0,
        passage_text="پاکستان ایک ملک ہے۔ اسلام آباد پاکستان کا دارالحکومت ہے۔",
        token_count=9,
    )


class EvidenceTests(unittest.TestCase):
    def test_urdu_sentence_split_preserves_evidence(self) -> None:
        self.assertEqual(
            split_sentences("ایک جملہ ہے۔ دوسرا جملہ ہے۔"), ["ایک جملہ ہے۔", "دوسرا جملہ ہے۔"]
        )

    def test_answer_is_exact_evidence_with_source(self) -> None:
        item = passage()
        result = SearchResult("p1", 1.0, 1, "test")
        answer = ExtractiveAnswerer(FixedEncoder(), max_sentences=1).answer(
            "پاکستان کا دارالحکومت", [result], {"p1": item}
        )
        self.assertTrue(answer.supported)
        self.assertEqual(answer.answer, "اسلام آباد پاکستان کا دارالحکومت ہے۔")
        self.assertEqual(answer.source_url, item.url)
        self.assertEqual(answer.answer, answer.evidence[0].text)

    def test_no_candidates_abstains_without_source(self) -> None:
        answer = ExtractiveAnswerer(FixedEncoder()).answer("نامعلوم سوال", [], {})
        self.assertFalse(answer.supported)
        self.assertEqual(answer.evidence, ())
        self.assertIsNone(answer.source_url)
        self.assertEqual(answer.abstention_reason, "no_retrieved_evidence")

    def test_low_similarity_abstains_without_unsupported_answer(self) -> None:
        item = passage()
        result = SearchResult("p1", 1.0, 1, "test")
        answer = ExtractiveAnswerer(OrthogonalEncoder(), similarity_threshold=0.9).answer(
            "نامعلوم سوال", [result], {"p1": item}, evidence_queries=["unrelated"]
        )
        self.assertFalse(answer.supported)
        self.assertEqual(answer.evidence, ())
        self.assertIsNotNone(answer.abstention_reason)

    def test_sentence_validator_selects_matching_evidence_type(self) -> None:
        passage = Passage(
            passage_id="p1",
            article_id="a1",
            title="محمد علی جناح",
            url="https://example.test/jinnah",
            domain="history",
            passage_index=0,
            passage_text="وہ ایک سیاسی رہنما تھے۔ اسلام آباد میں 25 دسمبر 1876 کو پیدا ہوئے۔",
            token_count=12,
        )
        candidate = SearchResult("p1", 0.9, 1, "reranker", ("reranker",))
        answer = ExtractiveAnswerer(FixedEncoder(), max_sentences=1).answer(
            "وہ کب پیدا ہوئے",
            [candidate],
            {"p1": passage},
            sentence_validator=lambda sentence: any(character.isdigit() for character in sentence),
        )

        self.assertTrue(answer.supported)
        self.assertIn("1876", answer.answer)

    def test_candidate_depth_prevents_unvalidated_lower_source_from_answering(self) -> None:
        top = Passage("p1", "a1", "اوّل", "url1", "general", 0, "غیر متعلق متن۔", 3)
        lower = Passage(
            "p2",
            "a2",
            "دوسرا",
            "url2",
            "general",
            0,
            "اسلام آباد پاکستان کا دارالحکومت ہے۔",
            5,
        )
        candidates = [
            SearchResult("p1", 0.9, 1, "reranker"),
            SearchResult("p2", 0.8, 2, "reranker"),
        ]

        answer = ExtractiveAnswerer(FixedEncoder(), candidate_depth=1).answer(
            "پاکستان کا دارالحکومت", candidates, {"p1": top, "p2": lower}
        )

        self.assertFalse(answer.supported)


if __name__ == "__main__":
    unittest.main()
