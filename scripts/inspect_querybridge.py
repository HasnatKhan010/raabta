"""Print QueryBridge variants and accept/reject reasons for one query."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from raabta.querybridge.bridge import QueryBridge, SupportingLexiconTransliterator
from raabta.retrieval.dense import E5Encoder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument(
        "--lexicon", type=Path, default=Path("artifacts/metadata/transliteration_lexicon.json")
    )
    parser.add_argument("--threshold", type=float, default=0.55)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    encoder = E5Encoder(
        "intfloat/multilingual-e5-small",
        "d1d99a1efae6779390caba937d92c54b5bc70e51",
        local_files_only=True,
    )
    bridge = QueryBridge(SupportingLexiconTransliterator(args.lexicon), encoder, args.threshold)
    print(
        json.dumps(
            [asdict(variant) for variant in bridge.generate(args.query)],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
