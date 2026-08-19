"""Evaluate the three frozen baselines on the development split only."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.evaluation.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from raabta.querybridge.transliteration import single_transliteration
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.fusion import reciprocal_rank_fusion
from raabta.retrieval.lexical import BM25Retriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--details", type=Path)
    parser.add_argument("--split", choices=["development"], default="development")
    parser.add_argument("--model", default="intfloat/multilingual-e5-small")
    parser.add_argument("--revision", default="d1d99a1efae6779390caba937d92c54b5bc70e51")
    return parser.parse_args()


def percentile_95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]


def main() -> None:
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
    embeddings = np.load(args.embeddings, allow_pickle=False, mmap_mode="r")
    encoder = E5Encoder(args.model, args.revision, local_files_only=True)
    dense_retriever = DenseRetriever(passages, embeddings, encoder)
    bm25 = BM25Retriever(passages)
    with args.diagnostic.open(encoding="utf-8-sig", newline="") as handle:
        queries = [row for row in csv.DictReader(handle) if row["split"] == args.split]

    measurements: dict[str, list[dict[str, float]]] = defaultdict(list)
    detail_rows = []
    for index, row in enumerate(queries, start=1):
        query = row["roman_urdu_query"]
        gold = {row["gold_passage_id"]}

        started = time.perf_counter()
        dense = dense_retriever.search(query, top_k=20)
        dense_ms = (time.perf_counter() - started) * 1000

        started = time.perf_counter()
        transliterated = single_transliteration(query)
        single = bm25.search(transliterated, top_k=10, route="single_transliteration_bm25")
        single_ms = (time.perf_counter() - started) * 1000

        started = time.perf_counter()
        raw_bm25 = bm25.search(query, top_k=20)
        hybrid = reciprocal_rank_fusion({"bm25": raw_bm25, "dense": dense}, constant=60, top_k=10)
        hybrid_ms = dense_ms + (time.perf_counter() - started) * 1000

        query_detail = {
            "query_id": row["query_id"],
            "query_type": row["query_type"],
            "systems": {},
        }
        for system, results, latency in (
            ("direct_dense", dense, dense_ms),
            ("single_transliteration_bm25", single, single_ms),
            ("standard_hybrid", hybrid, hybrid_ms),
        ):
            ranked = [result.passage_id for result in results]
            row_metrics = {
                "recall_at_1": recall_at_k(ranked, gold, 1),
                "recall_at_5": recall_at_k(ranked, gold, 5),
                "recall_at_10": recall_at_k(ranked, gold, 10),
                "mrr_at_10": reciprocal_rank(ranked, gold, 10),
                "ndcg_at_10": ndcg_at_k(ranked, gold, 10),
                "latency_ms": latency,
            }
            measurements[system].append(row_metrics)
            query_detail["systems"][system] = {
                **row_metrics,
                "gold_rank": next(
                    (rank for rank, passage_id in enumerate(ranked, start=1) if passage_id in gold),
                    None,
                ),
            }
        detail_rows.append(query_detail)
        if index % 20 == 0:
            print(f"Evaluated {index}/{len(queries)} development queries", flush=True)

    systems = {}
    for system, rows in measurements.items():
        systems[system] = {
            metric: round(statistics.fmean(row[metric] for row in rows), 6)
            for metric in ("recall_at_1", "recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
        }
        latencies = [row["latency_ms"] for row in rows]
        systems[system]["mean_latency_ms"] = round(statistics.fmean(latencies), 3)
        systems[system]["p95_latency_ms"] = round(percentile_95(latencies), 3)

    output = {
        "status": "development_only_project_verified",
        "queries": len(queries),
        "split": args.split,
        "test_queries_used": 0,
        "model": args.model,
        "revision": args.revision,
        "systems": systems,
        "limitation": "Development-set measurements; the separate test split is not used.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.details:
        args.details.parent.mkdir(parents=True, exist_ok=True)
        with args.details.open("w", encoding="utf-8", newline="\n") as handle:
            for row in detail_rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
