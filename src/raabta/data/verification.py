"""Phase-1-only corpus checks; this module is not a retrieval baseline."""

from __future__ import annotations

from collections.abc import Iterable

from raabta.data.models import Passage
from raabta.preprocessing.text import normalize_urdu_text


def find_literal_matches(passages: Iterable[Passage], query: str) -> list[Passage]:
    """Confirm known evidence survived preprocessing and chunking via literal matching."""

    normalized_query = normalize_urdu_text(query)
    if not normalized_query:
        raise ValueError("query must not be empty")
    return [passage for passage in passages if normalized_query in passage.passage_text]
