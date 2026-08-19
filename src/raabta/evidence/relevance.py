"""Conservative relevance checks that reject plausible-looking junk answers."""

from __future__ import annotations

import re
from dataclasses import dataclass

_DATE_WORDS = {
    "جنوری",
    "فروری",
    "مارچ",
    "اپریل",
    "مئی",
    "جون",
    "جولائی",
    "اگست",
    "ستمبر",
    "اکتوبر",
    "نومبر",
    "دسمبر",
}
_CURRENCY_MARKERS = {
    "$",
    "€",
    "£",
    "pkr",
    "price",
    "قیمت",
    "روپے",
    "روپیہ",
    "ڈالر",
    "یورو",
}
_LOCATION_MARKERS = {
    "شہر",
    "صوبہ",
    "ملک",
    "علاقہ",
    "واقع",
    "دارالحکومت",
    "ضلع",
}
_CAPITAL_PATTERN = re.compile(r"دار\s*الحکومت|\bcapital\b", flags=re.IGNORECASE)
_STOPWORDS = {
    "a",
    "about",
    "are",
    "batao",
    "btao",
    "hai",
    "hain",
    "how",
    "hy",
    "is",
    "ka",
    "kab",
    "kahan",
    "ke",
    "ki",
    "kia",
    "kon",
    "kya",
    "main",
    "me",
    "mein",
    "what",
    "when",
    "where",
    "who",
    "ہے",
    "ہیں",
    "کا",
    "کب",
    "کہاں",
    "کے",
    "کی",
    "کیا",
    "کون",
    "میں",
    "معلومات",
}


@dataclass(frozen=True, slots=True)
class RelevanceDecision:
    accepted: bool
    intent: str
    reason: str


def is_definition_query(query: str) -> bool:
    """Identify broad 'what is / tell me about' questions suited to lead sentences."""

    return bool(
        re.search(
            r"\b(?:what\s+is|kya|kia|bare\s+(?:me|mein)|batao|btao)\b|کیا ہے|کے بارے میں",
            query.casefold(),
        )
    )


def detect_intent(query: str) -> str:
    normalized = query.casefold()
    tokens = set(re.findall(r"[\w]+", normalized, flags=re.UNICODE))
    if tokens & {"price", "qeemat", "kimat", "قیمت"}:
        return "price"
    if tokens & {"kab", "kb", "when", "کب"}:
        return "date"
    if tokens & {"kitne", "kitni", "population", "abadi", "کتنے", "کتنی", "آبادی"}:
        return "quantity"
    if tokens & {
        "capital",
        "darulhukumat",
        "dar-ul-hukumat",
        "kahan",
        "where",
        "کہاں",
        "دارالحکومت",
        "province",
        "صوبہ",
    }:
        return "location"
    if tokens & {"kon", "kaun", "who", "کون"}:
        return "person"
    return "general"


def validate_answer_shape(query: str, answer: str) -> RelevanceDecision:
    """Require the evidence to contain the kind of fact asked for."""

    intent = detect_intent(query)
    folded = answer.casefold()
    tokens = set(re.findall(r"[\w$€£]+", folded, flags=re.UNICODE))
    has_number = bool(re.search(r"\d", answer))
    if re.search(r"مزید دیکھیے|حوالہ جات|بیرونی روابط", folded):
        return RelevanceDecision(False, intent, "evidence_is_navigation_boilerplate")
    asks_for_list = bool(re.search(r"\b(?:list|fehrist|fhrst)\b|فہرست", query.casefold()))
    if "فہرست" in tokens and not asks_for_list:
        return RelevanceDecision(False, intent, "evidence_is_list_description")
    if intent == "price" and not (tokens & _CURRENCY_MARKERS and has_number):
        return RelevanceDecision(False, intent, "price_evidence_has_no_currency_amount")
    if intent == "date":
        if not (has_number or tokens & _DATE_WORDS):
            return RelevanceDecision(False, intent, "date_evidence_has_no_date")
        query_folded = query.casefold()
        if re.search(r"\b(?:born|paida|peda)\b|پیدا", query_folded) and not re.search(
            r"پیدا|پیدائش|جنم|\bborn\b", folded
        ):
            return RelevanceDecision(False, intent, "date_evidence_missing_birth_relation")
        if re.search(r"\b(?:died|death|wafat)\b|وفات", query_folded) and not re.search(
            r"وفات|انتقال|موت|\bdied\b|\bdeath\b", folded
        ):
            return RelevanceDecision(False, intent, "date_evidence_missing_death_relation")
    if intent == "quantity" and not has_number:
        return RelevanceDecision(False, intent, "quantity_evidence_has_no_number")
    if intent == "location":
        has_location_marker = bool(tokens & _LOCATION_MARKERS) or bool(
            re.search(r"دار\s+الحکومت", folded)
        )
        if not has_location_marker:
            return RelevanceDecision(False, intent, "location_evidence_has_no_location_marker")
        asks_capital = bool(_CAPITAL_PATTERN.search(query))
        answer_has_capital = bool(_CAPITAL_PATTERN.search(answer))
        if asks_capital and not answer_has_capital:
            return RelevanceDecision(False, intent, "location_evidence_missing_capital_relation")
        asks_for_historical = bool(
            re.search(
                r"\b(?:first|former|old|pehla|pehli|sabiq)\b|پہلا|پہلی|سابق", query.casefold()
            )
        )
        historical_answer = bool(re.search(r"اس سے پہلے|سابق|\b(?:تھا|تھی|تھے)\b", folded))
        if asks_capital and not asks_for_historical and historical_answer and "ہے" not in tokens:
            return RelevanceDecision(
                False, intent, "location_evidence_is_historical_for_current_question"
            )
        if asks_capital and not asks_for_historical and not tokens & {"ہے", "ہیں"}:
            return RelevanceDecision(
                False, intent, "location_evidence_missing_current_capital_statement"
            )
    return RelevanceDecision(True, intent, "answer_shape_matches_query")


def content_token_overlap(query: str, evidence: str) -> tuple[int, float]:
    query_tokens = {
        token
        for token in re.findall(r"[\w]+", query.casefold(), flags=re.UNICODE)
        if len(token) > 1 and token not in _STOPWORDS and not token.isdigit()
    }
    evidence_tokens = set(re.findall(r"[\w]+", evidence.casefold(), flags=re.UNICODE))
    overlap = query_tokens & evidence_tokens
    return len(overlap), len(overlap) / max(1, len(query_tokens))


def reranker_confidence(top_score: float, second_score: float | None = None) -> str:
    if top_score >= 0.72 and (second_score is None or top_score - second_score >= 0.04):
        return "high"
    if top_score >= 0.62:
        return "medium"
    return "low"
