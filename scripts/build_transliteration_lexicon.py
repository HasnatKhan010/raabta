"""Build an auditable token lexicon from aligned supporting data without gold queries."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from raabta.data.io import read_jsonl
from raabta.preprocessing.text import normalize_roman_urdu, normalize_urdu_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--minimum-frequency", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    aligned_rows = 0
    for record in read_jsonl(args.input):
        roman = re.findall(r"[a-z0-9]+", normalize_roman_urdu(str(record["Roman-Urdu text"])))
        urdu = normalize_urdu_text(str(record["Urdu text"])).split()
        if len(roman) != len(urdu) or not roman:
            continue
        aligned_rows += 1
        for roman_token, urdu_token in zip(roman, urdu, strict=True):
            counts[roman_token][urdu_token] += 1
    lexicon = {}
    for roman_token, candidates in counts.items():
        urdu_token, frequency = candidates.most_common(1)[0]
        if frequency >= args.minimum_frequency:
            lexicon[roman_token] = {
                "urdu": urdu_token,
                "frequency": frequency,
                "alternatives": len(candidates),
            }
    output = {
        "source": args.input.as_posix(),
        "method": "equal-token-count positional alignment",
        "aligned_rows": aligned_rows,
        "minimum_frequency": args.minimum_frequency,
        "entries": dict(sorted(lexicon.items())),
        "warning": "Development lexicon; positional alignment is noisy and requires drift filtering.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(lexicon)} entries from {aligned_rows} equal-length aligned rows")


if __name__ == "__main__":
    main()
