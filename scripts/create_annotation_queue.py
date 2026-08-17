"""Create a deterministic article queue for manual diagnostic-question annotation."""

from __future__ import annotations

import argparse
import csv
import hashlib
from collections import defaultdict
from pathlib import Path

from raabta.data.io import read_jsonl


def stable_key(article_id: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}\0{article_id}".encode()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--per-domain", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20250816)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in read_jsonl(args.articles):
        by_domain[str(record["domain"])].append(record)

    selected: list[dict[str, object]] = []
    for domain in sorted(by_domain):
        ranked = sorted(
            by_domain[domain], key=lambda row: stable_key(str(row["article_id"]), args.seed)
        )
        if len(ranked) < args.per_domain:
            raise ValueError(f"Domain {domain!r} has fewer than {args.per_domain} articles")
        selected.extend(ranked[: args.per_domain])

    fields = [
        "candidate_id",
        "article_id",
        "title",
        "url",
        "domain",
        "source_excerpt",
        "canonical_question",
        "roman_urdu_query",
        "urdu_query",
        "query_type",
        "noise_level",
        "gold_passage_id",
        "gold_evidence_text",
        "answerable",
        "notes",
        "split",
        "annotator",
        "verification_status",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index, record in enumerate(selected, start=1):
            writer.writerow(
                {
                    "candidate_id": f"candidate-{index:03d}",
                    "article_id": record["article_id"],
                    "title": record["title"],
                    "url": record["url"],
                    "domain": record["domain"],
                    "source_excerpt": str(record["clean_text"])[:600].replace("\n", " "),
                    "answerable": "true",
                    "verification_status": "draft",
                }
            )
    print(f"Wrote {len(selected)} annotation candidates across {len(by_domain)} domains")


if __name__ == "__main__":
    main()
