"""Deterministic evidence-first extractive answering with abstention."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from raabta.data.models import Passage
from raabta.retrieval.dense import Encoder, normalize_rows
from raabta.retrieval.models import SearchResult


@dataclass(frozen=True, slots=True)
class EvidenceSentence:
    passage_id: str
    article_id: str
    title: str
    url: str
    sentence_index: int
    text: str
    similarity: float
    retrieval_rank: int


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    query: str
    supported: bool
    answer: str
    evidence: tuple[EvidenceSentence, ...]
    source_title: str | None
    source_url: str | None
    abstention_reason: str | None


def split_sentences(text: str) -> list[str]:
    """Split Urdu/Latin prose without changing the source sentence text."""
    pieces = re.split(r"(?<=[۔.!?؟])\s+|[\r\n]+", text.strip())
    return [piece.strip() for piece in pieces if piece.strip()]


class ExtractiveAnswerer:
    def __init__(
        self,
        encoder: Encoder,
        *,
        similarity_threshold: float = 0.70,
        candidate_depth: int = 5,
        max_sentences: int = 2,
    ) -> None:
        if not 0 <= similarity_threshold <= 1:
            raise ValueError("similarity_threshold must be between 0 and 1")
        if candidate_depth <= 0 or max_sentences <= 0:
            raise ValueError("candidate_depth and max_sentences must be positive")
        self.encoder = encoder
        self.similarity_threshold = similarity_threshold
        self.candidate_depth = candidate_depth
        self.max_sentences = max_sentences

    def answer(
        self,
        query: str,
        candidates: list[SearchResult] | tuple[SearchResult, ...],
        passages_by_id: dict[str, Passage],
        evidence_queries: Sequence[str] | None = None,
    ) -> GroundedAnswer:
        if not query.strip():
            raise ValueError("query must not be empty")
        sentence_rows: list[tuple[SearchResult, Passage, int, str]] = []
        for candidate in candidates[: self.candidate_depth]:
            passage = passages_by_id.get(candidate.passage_id)
            if passage is None:
                continue
            sentence_rows.extend(
                (candidate, passage, index, sentence)
                for index, sentence in enumerate(split_sentences(passage.passage_text))
            )
        if not sentence_rows:
            return self._abstain(query, "no_retrieved_evidence")

        query_texts = list(dict.fromkeys(evidence_queries or [query]))
        texts = [f"query: {item}" for item in query_texts] + [
            f"passage: {row[3]}" for row in sentence_rows
        ]
        vectors = normalize_rows(self.encoder.encode(texts))
        query_vectors = vectors[: len(query_texts)]
        sentence_vectors = vectors[len(query_texts) :]
        similarities = (sentence_vectors @ query_vectors.T).max(axis=1)
        ranked = sorted(
            zip(sentence_rows, similarities, strict=True),
            key=lambda item: (-float(item[1]), item[0][0].rank, item[0][2]),
        )
        best_score = float(ranked[0][1])
        if best_score < self.similarity_threshold:
            return self._abstain(
                query,
                f"insufficient_evidence_similarity:{best_score:.6f}<{self.similarity_threshold:.6f}",
            )

        best_passage_id = ranked[0][0][1].passage_id
        same_passage = [item for item in ranked if item[0][1].passage_id == best_passage_id]
        selected = [same_passage[0]]
        while len(selected) < min(self.max_sentences, len(same_passage)):
            selected_indices = {item[0][2] for item in selected}
            adjacent = [
                item
                for item in same_passage
                if item not in selected
                and any(abs(item[0][2] - index) == 1 for index in selected_indices)
            ]
            pool = adjacent or [item for item in same_passage if item not in selected]
            selected.append(pool[0])
        selected.sort(key=lambda item: item[0][2])
        evidence = tuple(
            EvidenceSentence(
                passage_id=passage.passage_id,
                article_id=passage.article_id,
                title=passage.title,
                url=passage.url,
                sentence_index=sentence_index,
                text=sentence,
                similarity=round(float(similarity), 6),
                retrieval_rank=candidate.rank,
            )
            for (candidate, passage, sentence_index, sentence), similarity in selected
        )
        return GroundedAnswer(
            query=query,
            supported=True,
            answer=" ".join(item.text for item in evidence),
            evidence=evidence,
            source_title=evidence[0].title,
            source_url=evidence[0].url,
            abstention_reason=None,
        )

    @staticmethod
    def _abstain(query: str, reason: str) -> GroundedAnswer:
        return GroundedAnswer(
            query=query,
            supported=False,
            answer="دستیاب شواہد سے قابل اعتماد جواب نہیں ملا۔",
            evidence=(),
            source_title=None,
            source_url=None,
            abstention_reason=reason,
        )
