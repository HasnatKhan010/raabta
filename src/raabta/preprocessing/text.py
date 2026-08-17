"""Text normalization that always preserves the original input separately."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")
_ROMAN_PUNCTUATION = re.compile(r"[^a-z0-9\s?'’-]+")

# Small, auditable function-word map. Content words and names are never corrected here.
_ROMAN_FUNCTION_WORDS = {
    "ha": "hai",
    "hy": "hai",
    "he": "hai",
    "hain": "hain",
    "kia": "kya",
    "kiya": "kya",
    "kb": "kab",
    "bna": "bana",
    "k": "ke",
}


def normalize_whitespace(text: str) -> str:
    """Collapse Unicode whitespace without removing meaningful punctuation."""

    return _WHITESPACE.sub(" ", text).strip()


def normalize_urdu_text(text: str, unicode_form: str = "NFKC") -> str:
    """Normalize Unicode/control characters while retaining Urdu punctuation and text."""

    normalized = unicodedata.normalize(unicode_form, text)
    usable = "".join(
        char
        for char in normalized
        if unicodedata.category(char) not in {"Cc", "Cs"} or char in "\n\t"
    )
    return normalize_whitespace(usable)


def normalize_roman_urdu(text: str) -> str:
    """Create a conservative Roman-Urdu copy using only documented function-word rules."""

    lowered = unicodedata.normalize("NFKC", text).lower()
    punctuation_normalized = _ROMAN_PUNCTUATION.sub(" ", lowered)
    normalized = normalize_whitespace(punctuation_normalized)
    function_word_pattern = re.compile(
        r"\b(" + "|".join(map(re.escape, _ROMAN_FUNCTION_WORDS)) + r")\b"
    )
    return function_word_pattern.sub(
        lambda match: _ROMAN_FUNCTION_WORDS[match.group(0)], normalized
    )
