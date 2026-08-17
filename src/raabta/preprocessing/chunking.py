"""Overlapping, deterministic whitespace-token passage chunking."""

from __future__ import annotations

import hashlib

from raabta.data.models import Article, Passage


def _passage_id(article_id: str, passage_index: int, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8"), usedforsecurity=False).hexdigest()[:12]
    return f"{article_id}-p{passage_index:04d}-{digest}"


def chunk_article(article: Article, chunk_size: int, overlap: int) -> list[Passage]:
    """Split clean article text into stable word windows with provenance."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")

    tokens = article.clean_text.split()
    if not tokens:
        return []

    step = chunk_size - overlap
    passages: list[Passage] = []
    for passage_index, start in enumerate(range(0, len(tokens), step)):
        window = tokens[start : start + chunk_size]
        if not window:
            break
        text = " ".join(window)
        passages.append(
            Passage(
                passage_id=_passage_id(article.article_id, passage_index, text),
                article_id=article.article_id,
                title=article.title,
                url=article.url,
                domain=article.domain,
                passage_index=passage_index,
                passage_text=text,
                token_count=len(window),
            )
        )
        if start + chunk_size >= len(tokens):
            break
    return passages
