from __future__ import annotations

from raabta.evidence.relevance import (
    content_token_overlap,
    is_definition_query,
    reranker_confidence,
    validate_answer_shape,
)


def test_price_question_rejects_topical_text_without_an_amount() -> None:
    decision = validate_answer_shape(
        "iphone ki price kya hai",
        "آئی فون ایپل کمپنی کا ایک موبائل فون ہے۔",
    )
    assert not decision.accepted
    assert decision.reason == "price_evidence_has_no_currency_amount"


def test_date_question_requires_a_date_like_fact() -> None:
    assert not validate_answer_shape(
        "quaid e azam kab paida hue", "وہ پاکستان کے بانی تھے۔"
    ).accepted
    assert validate_answer_shape(
        "quaid e azam kab paida hue", "محمد علی جناح 25 دسمبر 1876ء کو پیدا ہوئے۔"
    ).accepted
    wrong_relation = validate_answer_shape(
        "quaid e azam kab paida hue",
        "محمد علی جناح 1913ء سے آل انڈیا مسلم لیگ کے سربراہ رہے۔",
    )
    assert not wrong_relation.accepted
    assert wrong_relation.reason == "date_evidence_missing_birth_relation"


def test_capital_question_requires_the_capital_relation() -> None:
    assert not validate_answer_shape(
        "pakistan ka capital kya hai", "پاکستان کا سب سے بڑا شہر کراچی ہے۔"
    ).accepted
    assert validate_answer_shape(
        "pakistan ka capital kya hai", "اسلام آباد پاکستان کا دارالحکومت ہے۔"
    ).accepted
    assert validate_answer_shape(
        "pakistan ka capital kya hai", "پاکستان کا قومی دار الحکومت اسلام آباد ہے۔"
    ).accepted
    assert not validate_answer_shape(
        "pakistan ka capital kya hai",
        "اس سے پہلے کراچی پاکستان کا دارالحکومت تھا۔",
    ).accepted
    assert not validate_answer_shape(
        "pakistan ka capital kya hai",
        "مزید دیکھیے پاکستان کے شہر، دارالحکومت اور آباد مقامات۔",
    ).accepted
    assert not validate_answer_shape(
        "pakistan ka capital kya hai",
        "یہ پاکستان کے قومی اور صوبائی دارالحکومتوں کی ایک فہرست ہے۔",
    ).accepted


def test_definition_query_detection() -> None:
    assert is_definition_query("soidn min nsaiit k bare me btao")
    assert is_definition_query("rajndr amrnath kia h")
    assert not is_definition_query("quaid e azam kab paida hue")


def test_content_overlap_ignores_question_filler() -> None:
    count, ratio = content_token_overlap(
        "پاکستان کا دارالحکومت کیا ہے", "اسلام آباد پاکستان کا دارالحکومت ہے۔"
    )
    assert count == 2
    assert ratio == 1.0


def test_reranker_confidence_bands_are_conservative() -> None:
    assert reranker_confidence(0.80, 0.60) == "high"
    assert reranker_confidence(0.65, 0.58) == "medium"
    assert reranker_confidence(0.60, 0.58) == "low"
    assert reranker_confidence(0.40, 0.20) == "low"
