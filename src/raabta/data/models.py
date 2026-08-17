"""Typed data contracts used throughout the retrieval pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Article:
    article_id: str
    title: str
    url: str
    raw_text: str
    clean_text: str
    domain: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Passage:
    passage_id: str
    article_id: str
    title: str
    url: str
    domain: str
    passage_index: int
    passage_text: str
    token_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DiagnosticRecord:
    query_id: str
    canonical_question: str
    roman_urdu_query: str
    urdu_query: str
    query_type: str
    noise_level: str
    gold_article_id: str
    gold_passage_id: str
    gold_evidence_text: str
    answerable: bool
    domain: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
