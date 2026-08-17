"""Controlled, traceable multi-query reformulation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from raabta.preprocessing.text import normalize_roman_urdu
from raabta.retrieval.dense import Encoder, normalize_rows


@dataclass(frozen=True, slots=True)
class QueryVariant:
    variant_id: str
    variant_type: str
    query_text: str
    generation_method: str
    source_query: str
    accepted: bool
    semantic_similarity: float
    decision_reason: str


class SupportingLexiconTransliterator:
    def __init__(self, path: Path) -> None:
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.entries = {key: value["urdu"] for key, value in payload["entries"].items()}

    def transliterate(self, query: str, *, normalize_input: bool = True) -> str:
        source = normalize_roman_urdu(query) if normalize_input else query.casefold().strip()
        tokens = re.findall(r"[a-z0-9]+|[^\w\s]", source)
        return " ".join(self.entries.get(token, token) for token in tokens)


class QueryBridge:
    def __init__(
        self,
        transliterator: SupportingLexiconTransliterator,
        encoder: Encoder,
        similarity_threshold: float = 0.55,
    ) -> None:
        self.transliterator = transliterator
        self.encoder = encoder
        self.similarity_threshold = similarity_threshold

    def generate(self, query: str) -> list[QueryVariant]:
        return self.generate_configured(query)

    def generate_configured(
        self,
        query: str,
        *,
        use_normalization: bool = True,
        use_transliteration: bool = True,
        use_expansion: bool = True,
    ) -> list[QueryVariant]:
        if not query.strip():
            raise ValueError("query must not be empty")
        original = query.strip()
        working = normalize_roman_urdu(query) if use_normalization else query.casefold().strip()
        candidates = [("original", original, "identity")]
        if use_normalization:
            candidates.append(("normalized_roman", working, "conservative_rules"))
        transformed = working
        if use_transliteration:
            transformed = self.transliterator.transliterate(
                working, normalize_input=use_normalization
            )
            candidates.append(
                (
                    "urdu_script",
                    transformed,
                    "supporting_lexicon_positional_alignment",
                )
            )
        if use_expansion:
            if use_transliteration:
                retrieval = re.sub(r"\b(کیا|ہے|ہیں|کب)\b", " ", transformed)
                suffix = "معلومات"
            else:
                retrieval = re.sub(r"\b(kya|kia|hai|hy|hain|kab)\b", " ", transformed)
                suffix = "maloomat"
            clean_retrieval = re.sub(r"\s+", " ", retrieval).strip()
            retrieval = f"{clean_retrieval} {suffix}".strip()
            candidates.append(("retrieval_oriented", retrieval, "controlled_question_word_removal"))
        texts = [f"query: {item[1]}" for item in candidates]
        vectors = normalize_rows(self.encoder.encode(texts))
        similarities = vectors @ vectors[0]
        variants = []
        seen: set[str] = set()
        for index, ((variant_type, text, method), similarity) in enumerate(
            zip(candidates, similarities, strict=True), start=1
        ):
            duplicate = text in seen
            accepted = not duplicate and (
                index == 1 or float(similarity) >= self.similarity_threshold
            )
            reason = (
                "accepted_original"
                if index == 1
                else "rejected_duplicate"
                if duplicate
                else "accepted_similarity_threshold"
                if accepted
                else "rejected_semantic_drift"
            )
            variants.append(
                QueryVariant(
                    f"v{index}",
                    variant_type,
                    text,
                    method,
                    query,
                    accepted,
                    round(float(similarity), 6),
                    reason,
                )
            )
            seen.add(text)
        return variants
