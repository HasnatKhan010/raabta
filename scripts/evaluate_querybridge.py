"""Evaluate QueryBridge retrieval on development records only."""

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
from raabta.retrieval.roman_title import RomanizedTitleRetriever


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--lexicon", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.55)
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
    bridge = QueryBridge(SupportingLexiconTransliterator(args.lexicon), encoder, args.threshold)
    retriever = MultiQueryRetriever(
        bridge,
        BM25Retriever(passages),
        DenseRetriever(passages, embeddings, encoder),
        roman_title=RomanizedTitleRetriever(passages),
    )
    with args.diagnostic.open(encoding="utf-8-sig", newline="") as handle:
        queries = [row for row in csv.DictReader(handle) if row["split"] == "development"]

    measurements = []
    accepted_counts = []
    for index, row in enumerate(queries, start=1):
        started = time.perf_counter()
        output = retriever.search(row["roman_urdu_query"], route_top_k=20, final_top_k=10)
        latency = (time.perf_counter() - started) * 1000
        ranked = [result.passage_id for result in output.results]
        gold = {row["gold_passage_id"]}
        measurements.append(
            {
                "recall_at_1": recall_at_k(ranked, gold, 1),
                "recall_at_5": recall_at_k(ranked, gold, 5),
                "recall_at_10": recall_at_k(ranked, gold, 10),
                "mrr_at_10": reciprocal_rank(ranked, gold, 10),
                "ndcg_at_10": ndcg_at_k(ranked, gold, 10),
                "latency_ms": latency,
            }
        )
        accepted_counts.append(sum(variant.accepted for variant in output.variants))
        if index % 20 == 0:
            print(f"Evaluated {index}/{len(queries)} QueryBridge queries", flush=True)

    result = {
        metric: round(statistics.fmean(row[metric] for row in measurements), 6)
        for metric in ("recall_at_1", "recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
    }
    latencies = [row["latency_ms"] for row in measurements]
    result.update(
        mean_latency_ms=round(statistics.fmean(latencies), 3),
        p95_latency_ms=round(p95(latencies), 3),
        mean_accepted_variants=round(statistics.fmean(accepted_counts), 3),
    )
    report = {
        "status": "development_only_project_verified",
        "system": "querybridge_roman_title_bm25_dense_rrf_no_reranker",
        "queries": len(queries),
        "test_queries_used": 0,
        "similarity_threshold": args.threshold,
        "result": result,
        "limitation": "Development-set measurements; the separate test split is not used.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
