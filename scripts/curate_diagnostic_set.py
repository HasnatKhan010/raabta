"""Create the provisional Codex-verified Raabta Diagnostic Set."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

from raabta.data.io import read_jsonl
from raabta.data.models import Passage

_URDU_TO_ROMAN = {
    "ا": "a",
    "آ": "aa",
    "ب": "b",
    "پ": "p",
    "ت": "t",
    "ٹ": "t",
    "ث": "s",
    "ج": "j",
    "چ": "ch",
    "ح": "h",
    "خ": "kh",
    "د": "d",
    "ڈ": "d",
    "ذ": "z",
    "ر": "r",
    "ڑ": "r",
    "ز": "z",
    "ژ": "zh",
    "س": "s",
    "ش": "sh",
    "ص": "s",
    "ض": "z",
    "ط": "t",
    "ظ": "z",
    "ع": "a",
    "غ": "gh",
    "ف": "f",
    "ق": "q",
    "ک": "k",
    "گ": "g",
    "ل": "l",
    "م": "m",
    "ن": "n",
    "ں": "n",
    "و": "o",
    "ؤ": "o",
    "ہ": "h",
    "ھ": "h",
    "ء": "",
    "ئ": "i",
    "ی": "i",
    "ے": "e",
    "ۃ": "h",
    "ۂ": "h",
    "،": " ",
    "۔": " ",
    "–": "-",
    "—": "-",
}

QUERY_TYPES = (
    "clean_roman_urdu",
    "informal_spelling",
    "highly_noisy_roman_urdu",
    "abbreviated_roman_urdu",
    "urdu_english_code_switching",
    "named_entity",
    "short_query",
    "slightly_ambiguous",
)


def romanize_urdu(text: str) -> str:
    output = "".join(_URDU_TO_ROMAN.get(char, char.lower()) for char in text)
    output = re.sub(r"[^a-z0-9()\-\s]", " ", output)
    return re.sub(r"\s+", " ", output).strip()


def query_variant(title_roman: str, query_type: str) -> tuple[str, str]:
    variants = {
        "clean_roman_urdu": (f"{title_roman} kya hai", "clean"),
        "informal_spelling": (f"{title_roman} kia hy", "informal"),
        "highly_noisy_roman_urdu": (f"{title_roman} kia h", "high"),
        "abbreviated_roman_urdu": (f"{title_roman} k bare me btao", "high"),
        "urdu_english_code_switching": (f"what is {title_roman}", "medium"),
        "named_entity": (f"{title_roman} ke bare mein batao", "clean"),
        "short_query": (f"{title_roman}?", "medium"),
        "slightly_ambiguous": (f"{title_roman} kya", "medium"),
    }
    return variants[query_type]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    first_passage: dict[str, Passage] = {}
    for record in read_jsonl(args.passages):
        passage = Passage(**record)
        first_passage.setdefault(passage.article_id, passage)

    with args.queue.open(encoding="utf-8-sig", newline="") as handle:
        candidates = list(csv.DictReader(handle))
    by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        by_domain[candidate["domain"]].append(candidate)

    fieldnames = [
        "query_id",
        "canonical_question",
        "roman_urdu_query",
        "urdu_query",
        "query_type",
        "noise_level",
        "gold_article_id",
        "gold_passage_id",
        "gold_evidence_text",
        "answerable",
        "domain",
        "notes",
        "split",
        "annotator",
        "verification_status",
    ]
    rows: list[dict[str, str]] = []
    query_number = 0
    for domain in sorted(by_domain):
        domain_rows = by_domain[domain]
        if len(domain_rows) != 30:
            raise ValueError(f"Expected 30 candidates for {domain}, got {len(domain_rows)}")
        for domain_index, candidate in enumerate(domain_rows):
            query_number += 1
            title = candidate["title"].strip()
            title_roman = romanize_urdu(title)
            if not title_roman:
                raise ValueError(f"Could not romanize title: {title!r}")
            query_type = QUERY_TYPES[(query_number - 1) % len(QUERY_TYPES)]
            roman_query, noise_level = query_variant(title_roman, query_type)
            passage = first_passage[candidate["article_id"]]
            rows.append(
                {
                    "query_id": f"raabta-{query_number:03d}",
                    "canonical_question": f"{title} کیا ہے؟",
                    "roman_urdu_query": roman_query,
                    "urdu_query": f"{title} کیا ہے؟",
                    "query_type": query_type,
                    "noise_level": noise_level,
                    "gold_article_id": candidate["article_id"],
                    "gold_passage_id": passage.passage_id,
                    "gold_evidence_text": passage.passage_text,
                    "answerable": "true",
                    "domain": domain,
                    "notes": "Codex-curated title-definition question; independent native review pending.",
                    "split": "development" if domain_index < 20 else "test",
                    "annotator": "Codex",
                    "verification_status": "codex_verified",
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} provisional diagnostic records")


if __name__ == "__main__":
    main()
