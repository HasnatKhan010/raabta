from __future__ import annotations

from raabta.data.models import Passage
from raabta.retrieval.roman_title import RomanizedTitleRetriever, normalize_roman_title


def make_passage(identifier: str, article: str, title: str, index: int = 0) -> Passage:
    return Passage(
        identifier,
        article,
        title,
        f"https://example.test/{article}",
        "general",
        index,
        f"{title} کے بارے میں مستند متن۔",
        5,
    )


def test_normalization_removes_question_filler_but_keeps_entity() -> None:
    assert normalize_roman_title("Quaid-e-Azam ke bare mein batao") == "quaid e azam"


def test_romanized_title_route_matches_noisy_entity_and_deduplicates_articles() -> None:
    passages = [
        make_passage("jinnah-p0", "jinnah", "محمد علی جناح"),
        make_passage("jinnah-p1", "jinnah", "محمد علی جناح", 1),
        make_passage("iqbal-p0", "iqbal", "علامہ اقبال"),
    ]
    aliases = {"محمد علی جناح": "mhmd ali jnah", "علامہ اقبال": "allama iqbal"}
    retriever = RomanizedTitleRetriever(passages, romanizer=aliases.__getitem__)

    results = retriever.search("mohammad ali jinnah kab paida hue", top_k=5)

    assert results[0].passage_id == "jinnah-p0"
    assert sum(item.passage_id.startswith("jinnah") for item in results) == 1
    assert results[0].route == "roman_title"
    assert retriever.similarity("mohammad ali jinnah", "jinnah-p0") > 0.3
