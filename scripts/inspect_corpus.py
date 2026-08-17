"""Validate Phase 1 corpus invariants and emit a reproducibility manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path

from raabta.data.io import read_jsonl


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_articles(path: Path) -> dict[str, object]:
    identifiers: set[str] = set()
    domains: Counter[str] = Counter()
    token_counts: list[int] = []
    invalid = 0
    for record in read_jsonl(path):
        required = {"article_id", "title", "url", "raw_text", "clean_text", "domain"}
        if not required.issubset(record) or not record["article_id"] or not record["clean_text"]:
            invalid += 1
            continue
        identifiers.add(str(record["article_id"]))
        domains[str(record["domain"])] += 1
        token_counts.append(len(str(record["clean_text"]).split()))

    total = sum(domains.values())
    if invalid or total != len(identifiers):
        raise ValueError(
            f"Article validation failed: invalid={invalid}, duplicates={total-len(identifiers)}"
        )
    return {
        "path": path.as_posix(),
        "sha256": _sha256(path),
        "articles": total,
        "domains": dict(sorted(domains.items())),
        "tokens": {
            "minimum": min(token_counts),
            "median": statistics.median(token_counts),
            "mean": round(statistics.fmean(token_counts), 2),
            "maximum": max(token_counts),
        },
    }


def inspect_passages(path: Path, expected_articles: int) -> dict[str, object]:
    passage_ids: set[str] = set()
    article_ids: set[str] = set()
    token_counts: list[int] = []
    invalid = 0
    for record in read_jsonl(path):
        required = {
            "passage_id",
            "article_id",
            "title",
            "url",
            "domain",
            "passage_index",
            "passage_text",
            "token_count",
        }
        if not required.issubset(record) or not record["passage_text"]:
            invalid += 1
            continue
        passage_ids.add(str(record["passage_id"]))
        article_ids.add(str(record["article_id"]))
        token_count = int(record["token_count"])
        if token_count != len(str(record["passage_text"]).split()):
            invalid += 1
        token_counts.append(token_count)

    if invalid or len(passage_ids) != len(token_counts) or len(article_ids) != expected_articles:
        raise ValueError(
            "Passage validation failed: "
            f"invalid={invalid}, duplicates={len(token_counts)-len(passage_ids)}, "
            f"represented_articles={len(article_ids)}"
        )
    return {
        "path": path.as_posix(),
        "sha256": _sha256(path),
        "passages": len(passage_ids),
        "represented_articles": len(article_ids),
        "tokens": {
            "minimum": min(token_counts),
            "median": statistics.median(token_counts),
            "mean": round(statistics.fmean(token_counts), 2),
            "maximum": max(token_counts),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--articles", type=Path, required=True)
    parser.add_argument("--passages", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    article_summary = inspect_articles(args.articles)
    manifest = {
        "articles": article_summary,
        "passage_variants": [
            inspect_passages(path, int(article_summary["articles"])) for path in args.passages
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
