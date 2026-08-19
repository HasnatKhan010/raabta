"""Checkpointed depth-limited reranker evaluation on development data only."""

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
from raabta.evaluation.metrics import ndcg_at_k, recall_at_k, reciprocal_rank
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
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--depth", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=4)
    return parser.parse_args()


def metrics(ranked: list[str], gold: set[str]) -> dict[str, float]:
    return {
        "recall_at_1": recall_at_k(ranked, gold, 1),
        "recall_at_5": recall_at_k(ranked, gold, 5),
        "recall_at_10": recall_at_k(ranked, gold, 10),
        "mrr_at_10": reciprocal_rank(ranked, gold, 10),
        "ndcg_at_10": ndcg_at_k(ranked, gold, 10),
    }


def main() -> None:
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
    by_id = {item.passage_id: item for item in passages}
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
    reranker = MultilingualReranker(
        "Alibaba-NLP/gte-multilingual-reranker-base",
        "a6258e9d2b1a11aa7bccdff9efde562bbca4393d",
        code_revision="40ced75c3017eb27626c9d4ea981bde21a2662f4",
        local_files_only=True,
        batch_size=args.batch_size,
    )
    with args.diagnostic.open(encoding="utf-8-sig", newline="") as handle:
        queries = [row for row in csv.DictReader(handle) if row["split"] == "development"]

    completed = {}
    if args.checkpoint.exists():
        for record in read_jsonl(args.checkpoint):
            if int(record["depth"]) != args.depth:
                raise ValueError("Checkpoint depth does not match requested depth")
            completed[str(record["query_id"])] = record
    args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with args.checkpoint.open("a", encoding="utf-8", newline="\n") as checkpoint:
        for index, row in enumerate(queries, start=1):
            if row["query_id"] in completed:
                continue
            retrieve_started = time.perf_counter()
            output = retriever.search(
                row["roman_urdu_query"], route_top_k=args.depth, final_top_k=args.depth
            )
            retrieval_ms = (time.perf_counter() - retrieve_started) * 1000
            candidates = list(output.results[: args.depth])
            rerank_started = time.perf_counter()
            reranked = reranker.rerank(row["roman_urdu_query"], candidates, by_id)
            rerank_ms = (time.perf_counter() - rerank_started) * 1000
            gold = {row["gold_passage_id"]}
            record = {
                "query_id": row["query_id"],
                "query_type": row["query_type"],
                "depth": args.depth,
                "before": metrics([item.passage_id for item in candidates], gold),
                "after": metrics([item.passage_id for item in reranked], gold),
                "gold_before": next(
                    (item.rank for item in candidates if item.passage_id in gold), None
                ),
                "gold_after": next(
                    (item.rank for item in reranked if item.passage_id in gold), None
                ),
                "retrieval_ms": round(retrieval_ms, 3),
                "rerank_ms": round(rerank_ms, 3),
            }
            checkpoint.write(json.dumps(record, sort_keys=True) + "\n")
            checkpoint.flush()
            completed[row["query_id"]] = record
            if index % 5 == 0:
                print(f"Checkpointed {len(completed)}/{len(queries)} queries", flush=True)

    rows = [completed[row["query_id"]] for row in queries]
    metric_names = ("recall_at_1", "recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
    report = {
        "status": "development_only_project_verified",
        "queries": len(rows),
        "test_queries_used": 0,
        "depth": args.depth,
        "batch_size": args.batch_size,
        "model": "Alibaba-NLP/gte-multilingual-reranker-base",
        "revision": "a6258e9d2b1a11aa7bccdff9efde562bbca4393d",
        "code_revision": "40ced75c3017eb27626c9d4ea981bde21a2662f4",
        "before_reranking": {
            name: round(statistics.fmean(row["before"][name] for row in rows), 6)
            for name in metric_names
        },
        "after_reranking": {
            name: round(statistics.fmean(row["after"][name] for row in rows), 6)
            for name in metric_names
        },
        "mean_retrieval_ms": round(statistics.fmean(row["retrieval_ms"] for row in rows), 3),
        "mean_rerank_ms": round(statistics.fmean(row["rerank_ms"] for row in rows), 3),
        "resident_memory_mb": round(psutil.Process().memory_info().rss / 1024**2, 2),
        "limitation": "Development-set measurements; the separate test split is not used.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
