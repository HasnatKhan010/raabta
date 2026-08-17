"""Verify that known evidence survives the Phase 1 corpus pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.data.verification import find_literal_matches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--query", required=True)
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
    matches = find_literal_matches(passages, args.query)
    if not matches:
        raise SystemExit("No literal match found; Phase 1 acceptance check failed.")
    first = matches[0]
    print(f"PASS: {first.passage_id} | {first.title} | {first.url}")
    print(first.passage_text)


if __name__ == "__main__":
    main()
