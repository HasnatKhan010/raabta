"""Run local QueryBridge retrieval and return a traceable extractive answer."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.evidence.extractive import ExtractiveAnswerer
from raabta.querybridge.bridge import QueryBridge, SupportingLexiconTransliterator
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.multiquery import MultiQueryRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument(
        "--passages", type=Path, default=Path("data/processed/passages_150_30.jsonl")
    )
    parser.add_argument(
        "--embeddings", type=Path, default=Path("artifacts/embeddings/e5_small_150_30.npy")
    )
    parser.add_argument(
        "--lexicon", type=Path, default=Path("artifacts/metadata/transliteration_lexicon.json")
    )
    parser.add_argument("--threshold", type=float, default=0.70)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    passages = [Passage(**row) for row in read_jsonl(args.passages)]
    passages_by_id = {passage.passage_id: passage for passage in passages}
    embeddings = np.load(args.embeddings, allow_pickle=False, mmap_mode="r")
    encoder = E5Encoder(
        "intfloat/multilingual-e5-small",
        "d1d99a1efae6779390caba937d92c54b5bc70e51",
        local_files_only=True,
    )
    bridge = QueryBridge(SupportingLexiconTransliterator(args.lexicon), encoder, 0.55)
    retriever = MultiQueryRetriever(
        bridge, BM25Retriever(passages), DenseRetriever(passages, embeddings, encoder)
    )
    started = time.perf_counter()
    retrieval = retriever.search(args.query, route_top_k=20, final_top_k=10)
    retrieval_ms = (time.perf_counter() - started) * 1000
    started = time.perf_counter()
    answer = ExtractiveAnswerer(encoder, similarity_threshold=args.threshold).answer(
        args.query,
        retrieval.results,
        passages_by_id,
        evidence_queries=[variant.query_text for variant in retrieval.variants if variant.accepted],
    )
    answer_ms = (time.perf_counter() - started) * 1000
    payload = {
        **asdict(answer),
        "query_variants": [asdict(item) for item in retrieval.variants],
        "retrieval_trace": [asdict(item) for item in retrieval.results],
        "latency_ms": {
            "retrieval": round(retrieval_ms, 3),
            "answer_selection": round(answer_ms, 3),
            "total": round(retrieval_ms + answer_ms, 3),
        },
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
