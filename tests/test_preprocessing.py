from __future__ import annotations

import unittest

from raabta.preprocessing.text import normalize_roman_urdu, normalize_urdu_text


class TextNormalizationTests(unittest.TestCase):
    def test_urdu_normalization_preserves_punctuation(self) -> None:
        self.assertEqual(normalize_urdu_text("  لاہور  کیا ہے؟\n"), "لاہور کیا ہے؟")

    def test_urdu_normalization_removes_control_character(self) -> None:
        self.assertEqual(normalize_urdu_text("پاک\x00ستان"), "پاکستان")

    def test_roman_normalization_is_conservative_and_auditable(self) -> None:
        self.assertEqual(
            normalize_roman_urdu("Quaid-e-Azam K Pakistan kia hy?"),
            "quaid-e-azam ke pakistan kya hai?",
        )

    def test_raw_input_is_not_mutated(self) -> None:
        raw = "Lahore KI tareekh kia HY?"
        _ = normalize_roman_urdu(raw)
        self.assertEqual(raw, "Lahore KI tareekh kia HY?")


if __name__ == "__main__":
    unittest.main()
