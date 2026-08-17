"""Convert article JSONL into traceable overlapping passage JSONL."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from raabta.data.io import read_jsonl, write_jsonl
from raabta.data.models import Article
from raabta.data.selection import article_from_record
from raabta.preprocessing.chunking import chunk_article

LOGGER = logging.getLogger("raabta.build_corpus")


def _article(record: dict[str, object]) -> Article:
    if "article_id" not in record:
        return article_from_record(record)
    return Article(
        article_id=str(record["article_id"]),
        title=str(record["title"]),
        url=str(record["url"]),
        raw_text=str(record["raw_text"]),
        clean_text=str(record["clean_text"]),
        domain=str(record["domain"]),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--chunk-size", type=int, default=150)
    parser.add_argument("--overlap", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    article_count = 0
    passage_count = 0

    def passage_records():
        nonlocal article_count, passage_count
        for record in read_jsonl(args.input):
            article = _article(record)
            article_count += 1
            for passage in chunk_article(article, args.chunk_size, args.overlap):
                passage_count += 1
                yield passage.to_dict()

    write_jsonl(args.output, passage_records())
    LOGGER.info("Built %d passages from %d articles", passage_count, article_count)


if __name__ == "__main__":
    main()
