from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from raabta.querybridge.bridge import QueryBridge, SupportingLexiconTransliterator


class SimilarEncoder:
    def encode(self, texts):
        vectors = []
        for text in texts:
            vectors.append([1.0, 0.0] if "unrelated" not in text else [0.0, 1.0])
        return np.asarray(vectors, dtype=np.float32)


class QueryBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.lexicon_path = Path(self.directory.name) / "lexicon.json"
        self.lexicon_path.write_text(
            json.dumps(
                {
                    "entries": {
                        "pakistan": {"urdu": "پاکستان"},
                        "kya": {"urdu": "کیا"},
                        "hai": {"urdu": "ہے"},
                    }
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_generates_at_most_four_traceable_variants(self) -> None:
        bridge = QueryBridge(SupportingLexiconTransliterator(self.lexicon_path), SimilarEncoder())
        variants = bridge.generate("pakistan kya hy")
        self.assertEqual(len(variants), 4)
        self.assertEqual(variants[0].variant_type, "original")
        self.assertEqual(variants[2].query_text, "پاکستان کیا ہے")
        self.assertTrue(all(item.generation_method for item in variants))

    def test_empty_query_is_rejected(self) -> None:
        bridge = QueryBridge(SupportingLexiconTransliterator(self.lexicon_path), SimilarEncoder())
        with self.assertRaises(ValueError):
            bridge.generate("  ")

    def test_configured_generation_removes_requested_components(self) -> None:
        bridge = QueryBridge(SupportingLexiconTransliterator(self.lexicon_path), SimilarEncoder())
        variants = bridge.generate_configured(
            "Pakistan KYA hy",
            use_normalization=False,
            use_transliteration=False,
            use_expansion=True,
        )
        self.assertEqual(
            [item.variant_type for item in variants], ["original", "retrieval_oriented"]
        )
        self.assertEqual(variants[1].query_text, "pakistan maloomat")


if __name__ == "__main__":
    unittest.main()
