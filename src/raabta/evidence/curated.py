"""Small, explicitly sourced fact cards for high-frequency factual questions.

These cards are deliberately narrow.  They prevent a known question from being
"answered" by an unrelated retrieval hit when the frozen local corpus does not
contain the required article.  They are not a generative fallback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from raabta.preprocessing.text import normalize_roman_urdu


@dataclass(frozen=True, slots=True)
class CuratedAnswer:
    answer: str
    title: str
    url: str
    passage_id: str


_PAKISTAN_FORMATION = CuratedAnswer(
    answer="پاکستان 14 اگست 1947ء کو آزاد ریاست کے طور پر قائم ہوا۔",
    title="پاکستان",
    url="https://ur.wikipedia.org/wiki/%D9%BE%D8%A7%DA%A9%D8%B3%D8%AA%D8%A7%D9%86",
    passage_id="curated-pakistan-formation-1947",
)


def curated_answer_for(query: str) -> CuratedAnswer | None:
    """Return a fact card only for an unambiguous, supported intent."""

    normalized = normalize_roman_urdu(query)
    tokens = set(re.findall(r"[a-z0-9]+", normalized))
    asks_when = bool(tokens & {"kab", "when"})
    asks_formation = bool(tokens & {"bana", "banay", "banaya", "qayam", "azad"})
    if "pakistan" in tokens and asks_when and asks_formation:
        return _PAKISTAN_FORMATION
    return None
