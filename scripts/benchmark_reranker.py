"""Benchmark pinned multilingual reranking depths on development queries only."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from pathlib import Path

import numpy as np
import psutil

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.querybridge.bridge import QueryBridge, SupportingLexiconTransliterator
from raabta.reranking.multilingual import MultilingualReranker
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.multiquery import MultiQueryRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--lexicon", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--queries", type=int, default=6)
    parser.add_argument("--depths", type=int, nargs="+", default=[5, 10, 20])
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--model", default="Alibaba-NLP/gte-multilingual-reranker-base")
    parser.add_argument("--revision", default="a6258e9d2b1a11aa7bccdff9efde562bbca4393d")
    parser.add_argument("--code-revision", default="40ced75c3017eb27626c9d4ea981bde21a2662f4")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
    passages_by_id = {item.passage_id: item for item in passages}
    embeddings = np.load(args.embeddings, allow_pickle=False, mmap_mode="r")
    encoder = E5Encoder(
        "intfloat/multilingual-e5-small",
        "d1d99a1efae6779390caba937d92c54b5bc70e51",
        local_files_only=True,
    )
    retriever = MultiQueryRetriever(
        QueryBridge(SupportingLexiconTransliterator(args.lexicon), encoder, 0.55),
        BM25Retriever(passages),
        DenseRetriever(passages, embeddings, encoder),
    )
    with args.diagnostic.open(encoding="utf-8-sig", newline="") as handle:
        queries = [row for row in csv.DictReader(handle) if row["split"] == "development"][
            : args.queries
        ]

    load_started = time.perf_counter()
    reranker = MultilingualReranker(
        args.model,
        args.revision,
        code_revision=args.code_revision,
        batch_size=args.batch_size,
        local_files_only=args.local_files_only,
    )
    model_load_seconds = time.perf_counter() - load_started
    process = psutil.Process()
    measurements: dict[int, list[float]] = {depth: [] for depth in args.depths}
    examples = []
    for row in queries:
        retrieved = retriever.search(
            row["roman_urdu_query"], route_top_k=max(args.depths), final_top_k=max(args.depths)
        )
        for depth in args.depths:
            candidates = list(retrieved.results[:depth])
            started = time.perf_counter()
            reranked = reranker.rerank(row["roman_urdu_query"], candidates, passages_by_id)
            measurements[depth].append((time.perf_counter() - started) * 1000)
            if depth == max(args.depths):
                examples.append(
                    {
                        "query_id": row["query_id"],
                        "gold_before": next(
                            (
                                item.rank
                                for item in candidates
                                if item.passage_id == row["gold_passage_id"]
                            ),
                            None,
                        ),
                        "gold_after": next(
                            (
                                item.rank
                                for item in reranked
                                if item.passage_id == row["gold_passage_id"]
                            ),
                            None,
                        ),
                    }
                )
    report = {
        "status": "development_cpu_feasibility_benchmark",
        "model": args.model,
        "revision": args.revision,
        "code_revision": args.code_revision,
        "queries": len(queries),
        "test_queries_used": 0,
        "batch_size": args.batch_size,
        "model_load_seconds": round(model_load_seconds, 3),
        "resident_memory_mb_after_benchmark": round(process.memory_info().rss / 1024**2, 2),
        "depths": {
            str(depth): {
                "mean_ms": round(statistics.fmean(values), 3),
                "maximum_ms": round(max(values), 3),
            }
            for depth, values in measurements.items()
        },
        "examples": examples,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
