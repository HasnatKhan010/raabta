"""Run traceable baseline smoke queries without claiming evaluation metrics."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.querybridge.transliteration import single_transliteration
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.fusion import reciprocal_rank_fusion
from raabta.retrieval.lexical import BM25Retriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", default="intfloat/multilingual-e5-small")
    parser.add_argument("--revision", default="d1d99a1efae6779390caba937d92c54b5bc70e51")
    parser.add_argument("--cache", type=Path, default=Path("artifacts/models/huggingface"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
    by_id = {item.passage_id: item for item in passages}
    embeddings = np.load(args.embeddings, allow_pickle=False, mmap_mode="r")
    encoder = E5Encoder(args.model, args.revision, cache_folder=args.cache, local_files_only=True)
    dense = DenseRetriever(passages, embeddings, encoder)
    bm25 = BM25Retriever(passages)

    started = time.perf_counter()
    dense_results = dense.search(args.query, top_k=max(args.top_k, 20))
    bm25_results = bm25.search(args.query, top_k=max(args.top_k, 20))
    transliterated = single_transliteration(args.query)
    transliteration_results = bm25.search(
        transliterated, top_k=max(args.top_k, 20), route="single_transliteration_bm25"
    )
    hybrid = reciprocal_rank_fusion(
        {"bm25": bm25_results, "dense": dense_results}, constant=60, top_k=args.top_k
    )
    elapsed_ms = (time.perf_counter() - started) * 1000

    def present(results):
        return [
            {
                "rank": result.rank,
                "passage_id": result.passage_id,
                "title": by_id[result.passage_id].title,
                "url": by_id[result.passage_id].url,
                "score": round(result.score, 6),
                "routes": list(result.contributing_routes) or [result.route],
            }
            for result in results[: args.top_k]
        ]

    output = {
        "query": args.query,
        "single_transliteration": transliterated,
        "direct_dense": present(dense_results),
        "single_transliteration_bm25": present(transliteration_results),
        "standard_hybrid": present(hybrid),
        "total_smoke_latency_ms": round(elapsed_ms, 3),
        "warning": "Smoke output only; no gold relevance judgment or benchmark metric.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
