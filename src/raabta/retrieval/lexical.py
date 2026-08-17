"""Transparent BM25 lexical retrieval."""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from raabta.data.models import Passage
from raabta.retrieval.models import SearchResult

_TOKEN = re.compile(r"\w+", flags=re.UNICODE)


def lexical_tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.casefold())


class BM25Retriever:
    def __init__(self, passages: list[Passage]) -> None:
        if not passages:
            raise ValueError("passages must not be empty")
        self.passages = passages
        tokenized = [lexical_tokens(item.passage_text) for item in passages]
        self._token_sets = [set(tokens) for tokens in tokenized]
        self.index = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 10, route: str = "bm25") -> list[SearchResult]:
        tokens = lexical_tokens(query)
        if not tokens:
            raise ValueError("query must not be empty")
        scores = self.index.get_scores(tokens)
        query_token_set = set(tokens)
        indices = sorted(
            (index for index in range(len(scores)) if query_token_set & self._token_sets[index]),
            key=lambda index: (-scores[index], index),
        )[:top_k]
        return [
            SearchResult(self.passages[index].passage_id, float(scores[index]), rank, route)
            for rank, index in enumerate(indices, start=1)
        ]
