"""Small deterministic one-best baseline transliteration.

This intentionally limited lexicon is a baseline, not the final QueryBridge implementation.
Unknown tokens are preserved so failures remain observable.
"""

from __future__ import annotations

import re

from raabta.preprocessing.text import normalize_roman_urdu

_WORDS = {
    "pakistan": "پاکستان",
    "ka": "کا",
    "ki": "کی",
    "ke": "کے",
    "kya": "کیا",
    "hai": "ہے",
    "kab": "کب",
    "paida": "پیدا",
    "hue": "ہوئے",
    "lahore": "لاہور",
    "islamabad": "اسلام آباد",
    "capital": "دارالحکومت",
    "city": "شہر",
    "tareekh": "تاریخ",
    "quaid": "قائد",
    "azam": "اعظم",
    "pehle": "پہلے",
    "governor": "گورنر",
    "general": "جنرل",
    "bane": "بنے",
}


def single_transliteration(query: str) -> str:
    normalized = normalize_roman_urdu(query)
    tokens = re.findall(r"[a-z0-9]+|[^\w\s]", normalized, flags=re.UNICODE)
    if not tokens:
        raise ValueError("query must not be empty")
    return " ".join(_WORDS.get(token, token) for token in tokens)
