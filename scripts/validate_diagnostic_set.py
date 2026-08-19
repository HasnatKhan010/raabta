"""Validate diagnostic-set schema, frozen evidence, balance, and split integrity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from raabta.data.io import read_jsonl


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    passages = {record["passage_id"]: record for record in read_jsonl(args.passages)}
    with args.diagnostic.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not 150 <= len(rows) <= 200:
        raise ValueError(f"Expected 150-200 records, got {len(rows)}")
    ids = [row["query_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate query IDs")
    for row in rows:
        passage = passages.get(row["gold_passage_id"])
        if passage is None:
            raise ValueError(f"Missing passage for {row['query_id']}")
        if passage["article_id"] != row["gold_article_id"]:
            raise ValueError(f"Article mismatch for {row['query_id']}")
        if passage["passage_text"] != row["gold_evidence_text"]:
            raise ValueError(f"Evidence mismatch for {row['query_id']}")
        if not row["roman_urdu_query"].strip() or not row["urdu_query"].strip():
            raise ValueError(f"Empty query for {row['query_id']}")
    manifest = {
        "records": len(rows),
        "sha256": sha256(args.diagnostic),
        "splits": dict(sorted(Counter(row["split"] for row in rows).items())),
        "domains": dict(sorted(Counter(row["domain"] for row in rows).items())),
        "query_types": dict(sorted(Counter(row["query_type"] for row in rows).items())),
        "verification_status": dict(
            sorted(Counter(row["verification_status"] for row in rows).items())
        ),
        "evidence_contract": "all passage IDs, article IDs, and exact evidence texts matched",
        "limitation": "project-verified development set for assignment evaluation",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
