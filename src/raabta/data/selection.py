"""Deterministic project-domain labeling and bounded subset selection."""

from __future__ import annotations

import hashlib
import heapq
from collections.abc import Iterable, Mapping

from raabta.data.models import Article
from raabta.preprocessing.text import normalize_urdu_text

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "history": ("تاریخ", "سلطنت", "جنگ", "قدیم", "بادشاہ"),
    "geography": ("جغرافیہ", "شہر", "دریا", "پہاڑ", "صوبہ", "ضلع"),
    "science": ("سائنس", "طبیعیات", "کیمیا", "حیاتیات", "سیارہ", "تحقیق"),
    "culture": ("ثقافت", "ادب", "شاعری", "موسیقی", "زبان", "فن"),
    "pakistan": ("پاکستان", "پاکستانی", "اسلام آباد", "لاہور", "کراچی"),
}


def infer_project_domain(title: str, text: str) -> str:
    """Assign one auditable project label; these are not Wikipedia categories."""

    sample = f"{title} {text[:2000]}"
    scores = {
        domain: sum(sample.count(keyword) for keyword in keywords)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best_domain, best_score = max(scores.items(), key=lambda item: (item[1], item[0]))
    return best_domain if best_score > 0 else "general"


def article_from_record(record: Mapping[str, object]) -> Article:
    """Convert a Wikimedia-style record while preserving raw text."""

    raw_text = str(record.get("text", ""))
    title = str(record.get("title", ""))
    return Article(
        article_id=str(record.get("id", "")),
        title=title,
        url=str(record.get("url", "")),
        raw_text=raw_text,
        clean_text=normalize_urdu_text(raw_text),
        domain=infer_project_domain(title, raw_text),
    )


def _stable_priority(article: Article, seed: int) -> str:
    payload = f"{seed}\0{article.article_id}\0{article.title}".encode()
    return hashlib.sha256(payload).hexdigest()


def select_deterministic_subset(
    records: Iterable[Mapping[str, object]],
    subset_size: int,
    domains: set[str],
    seed: int,
    minimum_tokens: int,
) -> list[Article]:
    """Select the smallest stable hashes after deterministic eligibility filtering.

    This implementation is intentionally bounded to the requested subset workflow. It does
    not randomize by stream order and therefore reproduces the same output for the same
    source revision, seed, and filters.
    """

    if subset_size <= 0:
        raise ValueError("subset_size must be positive")

    # Negative integer priorities turn Python's min-heap into a bounded max-heap.
    # Only `subset_size` articles are retained, even while a large stream is scanned.
    eligible: list[tuple[int, str, Article]] = []
    for record in records:
        article = article_from_record(record)
        if article.domain not in domains or len(article.clean_text.split()) < minimum_tokens:
            continue
        priority = int(_stable_priority(article, seed), 16)
        entry = (-priority, article.article_id, article)
        if len(eligible) < subset_size:
            heapq.heappush(eligible, entry)
        elif priority < -eligible[0][0]:
            heapq.heapreplace(eligible, entry)

    ranked = sorted((-negative_priority, article) for negative_priority, _, article in eligible)
    return [article for _, article in ranked]
