"""Validate the bounded Roman-Urdu/Urdu development slice."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

from raabta.data.io import read_jsonl


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pairs: set[tuple[str, str]] = set()
    roman_values: set[str] = set()
    urdu_values: set[str] = set()
    roman_lengths: list[int] = []
    urdu_lengths: list[int] = []
    empty_rows = 0

    for record in read_jsonl(args.input):
        roman = str(record.get("Roman-Urdu text", "")).strip()
        urdu = str(record.get("Urdu text", "")).strip()
        if not roman or not urdu:
            empty_rows += 1
            continue
        pairs.add((roman, urdu))
        roman_values.add(roman)
        urdu_values.add(urdu)
        roman_lengths.append(len(roman.split()))
        urdu_lengths.append(len(urdu.split()))

    total = len(roman_lengths) + empty_rows
    if empty_rows:
        raise ValueError(f"Found {empty_rows} empty aligned rows")
    manifest = {
        "path": args.input.as_posix(),
        "sha256": file_sha256(args.input),
        "rows": total,
        "unique_pairs": len(pairs),
        "unique_roman_strings": len(roman_values),
        "unique_urdu_strings": len(urdu_values),
        "duplicate_pairs": total - len(pairs),
        "roman_tokens": {
            "minimum": min(roman_lengths),
            "median": statistics.median(roman_lengths),
            "mean": round(statistics.fmean(roman_lengths), 2),
            "maximum": max(roman_lengths),
        },
        "urdu_tokens": {
            "minimum": min(urdu_lengths),
            "median": statistics.median(urdu_lengths),
            "mean": round(statistics.fmean(urdu_lengths), 2),
            "maximum": max(urdu_lengths),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
