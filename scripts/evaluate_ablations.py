"""Evaluate retrieval-stage Raabta ablations on the development split only."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import time
from pathlib import Path

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.evaluation.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
from raabta.querybridge.bridge import QueryBridge, SupportingLexiconTransliterator
from raabta.retrieval.dense import DenseRetriever, E5Encoder
from raabta.retrieval.lexical import BM25Retriever
from raabta.retrieval.multiquery import MultiQueryRetriever

CONFIGURATIONS = {
    "full_no_reranker": {},
    "no_normalization": {"use_normalization": False},
    "no_transliteration": {"use_transliteration": False},
    "no_expansion": {"use_expansion": False},
    "no_bm25": {"use_bm25": False},
    "no_dense": {"use_dense": False},
    "no_fusion": {"use_fusion": False},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--lexicon", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--details", type=Path, required=True)
    return parser.parse_args()


def p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(0.95 * len(ordered)))]


def main() -> None:
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
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
        queries = [row for row in csv.DictReader(handle) if row["split"] == "development"]

    all_rows: list[dict] = []
    aggregates: dict[str, dict] = {}
    for config_name, options in CONFIGURATIONS.items():
        measurements = []
        for index, row in enumerate(queries, start=1):
            started = time.perf_counter()
            output = retriever.search(
                row["roman_urdu_query"], route_top_k=20, final_top_k=10, **options
            )
            latency_ms = (time.perf_counter() - started) * 1000
            ranked = [result.passage_id for result in output.results]
            gold = {row["gold_passage_id"]}
            metrics = {
                "recall_at_1": recall_at_k(ranked, gold, 1),
                "recall_at_5": recall_at_k(ranked, gold, 5),
                "recall_at_10": recall_at_k(ranked, gold, 10),
                "mrr_at_10": reciprocal_rank(ranked, gold, 10),
                "ndcg_at_10": ndcg_at_k(ranked, gold, 10),
                "latency_ms": latency_ms,
            }
            measurements.append(metrics)
            all_rows.append(
                {
                    "configuration": config_name,
                    "query_id": row["query_id"],
                    "query_type": row["query_type"],
                    "ranked_passage_ids": ranked,
                    "gold_rank": next(
                        (rank for rank, item in enumerate(ranked, 1) if item in gold), None
                    ),
                    "metrics": metrics,
                }
            )
            if index % 40 == 0:
                print(f"{config_name}: {index}/{len(queries)}", flush=True)
        summary = {
            metric: round(statistics.fmean(row[metric] for row in measurements), 6)
            for metric in ("recall_at_1", "recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
        }
        latencies = [row["latency_ms"] for row in measurements]
        summary["mean_latency_ms"] = round(statistics.fmean(latencies), 3)
        summary["p95_latency_ms"] = round(p95(latencies), 3)
        aggregates[config_name] = summary

    report = {
        "status": "provisional_codex_verified_development_only",
        "protocol": "retrieval-stage leave-one-component-out; reranker held absent",
        "queries": len(queries),
        "test_queries_used": 0,
        "configurations": aggregates,
        "no_reranking_comparison_source": "reports/tables/provisional_reranker_depth20.json",
        "limitation": (
            "The six retrieval-component controls isolate retrieval behavior before reranking; "
            "the separately measured no-reranking control isolates the reranker. Independent "
            "native-speaker review remains pending."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.details.parent.mkdir(parents=True, exist_ok=True)
    with args.details.open("w", encoding="utf-8", newline="\n") as handle:
        for row in all_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
