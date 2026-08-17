from __future__ import annotations

from raabta.evidence.curated import curated_answer_for


def test_pakistan_formation_question_has_a_verified_fact_card() -> None:
    answer = curated_answer_for("Pakistan kb bna")

    assert answer is not None
    assert answer.answer == "پاکستان 14 اگست 1947ء کو آزاد ریاست کے طور پر قائم ہوا۔"
    assert answer.title == "پاکستان"

    assert curated_answer_for("Pakistan kab bana") is not None


def test_other_pakistan_questions_remain_evidence_retrieval_queries() -> None:
    assert curated_answer_for("Pakistan ka capital kya hai") is None
    assert curated_answer_for("Pakistan kab bana") is not None
