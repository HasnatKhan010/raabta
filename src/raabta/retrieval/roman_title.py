"""Character-level retrieval over romanized Urdu article titles."""

from __future__ import annotations

import re
from collections.abc import Callable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from raabta.data.models import Passage
from raabta.retrieval.models import SearchResult

_QUESTION_FILLER = re.compile(
    r"\b(?:what|who|where|when|is|kya|kia|hai|hy|hain|h|ka|ki|ke|k|kab|kb|"
    r"kon|kaun|bare|me|mein|min|batao|btao)\b",
    flags=re.IGNORECASE,
)
_NON_ROMAN = re.compile(r"[^a-z0-9]+")


def normalize_roman_title(text: str) -> str:
    """Keep entity-bearing Roman text and remove common question boilerplate."""

    without_filler = _QUESTION_FILLER.sub(" ", text.casefold().replace("'", " "))
    return " ".join(_NON_ROMAN.sub(" ", without_filler).split())


class RomanizedTitleRetriever:
    """Match noisy Roman queries to one lead passage per romanized Urdu title.

    Urdu spelling hides short vowels, which makes character n-grams unusually useful:
    ``محمد`` romanizes as ``mhmd`` and still matches common inputs such as ``mohammad``.
    One lead passage per article prevents duplicate chunks from occupying the result list.
    """

    def __init__(
        self,
        passages: list[Passage],
        *,
        romanizer: Callable[[str], str] | None = None,
    ) -> None:
        if not passages:
            raise ValueError("passages must not be empty")
        if romanizer is None:
            from uroman import Uroman

            engine = Uroman()

            def romanize_urdu(text: str) -> str:
                return engine.romanize_string(text, lcode="urd")

            romanizer = romanize_urdu

        seen_articles: set[str] = set()
        self.passages: list[Passage] = []
        for passage in passages:
            if passage.article_id not in seen_articles:
                self.passages.append(passage)
                seen_articles.add(passage.article_id)
        aliases = [normalize_roman_title(romanizer(item.title)) for item in self.passages]
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            lowercase=False,
            sublinear_tf=True,
            norm="l2",
            dtype=np.float32,
        )
        self.matrix = self.vectorizer.fit_transform(aliases)
        self._index_by_passage_id = {
            passage.passage_id: index for index, passage in enumerate(self.passages)
        }

    def similarity(self, query: str, passage_id: str) -> float:
        """Return the character-level query/title similarity for one indexed lead passage."""

        index = self._index_by_passage_id.get(passage_id)
        normalized = normalize_roman_title(query)
        if index is None or not normalized:
            return 0.0
        query_vector = self.vectorizer.transform([normalized])
        return float((self.matrix[index] @ query_vector.T).toarray()[0, 0])

    def search(
        self,
        query: str,
        top_k: int = 10,
        route: str = "roman_title",
    ) -> list[SearchResult]:
        normalized = normalize_roman_title(query)
        if not normalized:
            return []
        query_vector = self.vectorizer.transform([normalized])
        scores = (self.matrix @ query_vector.T).toarray().ravel()
        positive = np.flatnonzero(scores > 0)
        ranked = sorted(positive, key=lambda index: (-float(scores[index]), int(index)))[:top_k]
        return [
            SearchResult(
                self.passages[index].passage_id,
                float(scores[index]),
                rank,
                route,
            )
            for rank, index in enumerate(ranked, start=1)
        ]
