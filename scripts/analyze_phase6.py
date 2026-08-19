"""Generate Phase 6 tables, figures, and a 30-case development failure audit."""

from __future__ import annotations

import argparse
import csv
import html
import json
import statistics
from collections import defaultdict
from pathlib import Path

from raabta.data.io import read_jsonl

METRICS = ("recall_at_1", "recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10")
TYPE_FAILURE = {
    "informal_spelling": "Roman spelling mismatch",
    "highly_noisy_roman_urdu": "excessive spelling noise",
    "urdu_english_code_switching": "code-switching failure",
    "named_entity": "named-entity mismatch",
    "short_query": "short ambiguous query",
    "slightly_ambiguous": "short ambiguous query",
    "abbreviated_roman_urdu": "Roman spelling mismatch",
    "clean_roman_urdu": "irrelevant retrieval",
}
IMPROVEMENTS = {
    "Roman spelling mismatch": "Learn spelling variants from reviewed Roman-Urdu pairs.",
    "excessive spelling noise": "Add a confidence-aware character-level normalizer.",
    "incorrect transliteration": "Use context-sensitive transliteration with calibrated alternatives.",
    "code-switching failure": "Detect language per token and preserve English entities/terms.",
    "named-entity mismatch": "Add alias tables and entity-aware candidate generation.",
    "short ambiguous query": "Add clarification or conservative query-context expansion.",
    "irrelevant retrieval": "Improve hard-negative training and corpus-aware term weighting.",
    "correct article but wrong passage": "Use article-aware passage aggregation and neighboring context.",
    "reranker failure": "Tune the reranker on reviewed hard negatives and calibrate depth.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--baseline-details", type=Path, required=True)
    parser.add_argument("--ablation-details", type=Path, required=True)
    parser.add_argument("--ablation-report", type=Path, required=True)
    parser.add_argument("--reranker-checkpoint", type=Path, required=True)
    parser.add_argument("--robustness-output", type=Path, required=True)
    parser.add_argument("--failures-output", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--latency-output", type=Path, required=True)
    parser.add_argument("--embedding-manifest", type=Path, required=True)
    parser.add_argument("--baseline-report", type=Path, required=True)
    parser.add_argument("--querybridge-report", type=Path, required=True)
    parser.add_argument("--reranker-report", type=Path, required=True)
    parser.add_argument("--reranker-benchmark", type=Path, required=True)
    return parser.parse_args()


def means(rows: list[dict]) -> dict[str, float]:
    return {metric: round(statistics.fmean(row[metric] for row in rows), 6) for metric in METRICS}


def bar_svg(title: str, labels: list[str], values: list[float], path: Path) -> None:
    width, height = 1000, 520
    left, top, chart_h = 230, 70, 370
    maximum = max(values) if values else 1.0
    scale = 650 / maximum if maximum else 1.0
    rows = []
    for index, (label, value) in enumerate(zip(labels, values, strict=True)):
        y = top + index * (chart_h / max(len(labels), 1))
        bar_h = min(28, chart_h / max(len(labels), 1) - 5)
        rows.append(
            f'<text x="{left - 12}" y="{y + bar_h * .75:.1f}" text-anchor="end" '
            f'font-size="14">{html.escape(label)}</text>'
            f'<rect x="{left}" y="{y:.1f}" width="{value * scale:.1f}" height="{bar_h:.1f}" '
            f'fill="#3765a3" rx="3"/>'
            f'<text x="{left + value * scale + 8:.1f}" y="{y + bar_h * .75:.1f}" '
            f'font-size="13">{value:.3f}</text>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="white"/>'
        f'<text x="{width/2}" y="35" text-anchor="middle" font-size="22" '
        f'font-family="sans-serif">{html.escape(title)}</text>'
        f'<g font-family="sans-serif">{"".join(rows)}</g>'
        '<text x="500" y="500" text-anchor="middle" font-family="sans-serif" font-size="13">'
        'Development split only; higher is better</text></svg>'
    )
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    args = parse_args()
    with args.diagnostic.open(encoding="utf-8-sig", newline="") as handle:
        diagnostic = {
            row["query_id"]: row for row in csv.DictReader(handle) if row["split"] == "development"
        }
    baseline = {row["query_id"]: row for row in read_jsonl(args.baseline_details)}
    reranker = {row["query_id"]: row for row in read_jsonl(args.reranker_checkpoint)}
    ablation_rows = list(read_jsonl(args.ablation_details))
    full_rows = {
        row["query_id"]: row for row in ablation_rows if row["configuration"] == "full_no_reranker"
    }
    expected = set(diagnostic)
    for name, actual in (
        ("baseline", set(baseline)),
        ("reranker", set(reranker)),
        ("full", set(full_rows)),
    ):
        if actual != expected:
            raise ValueError(f"{name} query IDs do not exactly match the development split")

    grouped: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for query_id, record in diagnostic.items():
        query_type = record["query_type"]
        for system, metrics in baseline[query_id]["systems"].items():
            grouped[query_type][system].append(metrics)
        grouped[query_type]["querybridge_no_reranker"].append(reranker[query_id]["before"])
        grouped[query_type]["querybridge_reranked"].append(reranker[query_id]["after"])
    robustness = {
        query_type: {
            system: {"queries": len(rows), **means(rows)}
            for system, rows in sorted(systems.items())
        }
        for query_type, systems in sorted(grouped.items())
    }
    robustness_report = {
        "status": "development_only_project_verified",
        "test_queries_used": 0,
        "query_types": robustness,
        "limitation": "Development-set engineering diagnostics; the separate test split is not used.",
    }
    args.robustness_output.parent.mkdir(parents=True, exist_ok=True)
    args.robustness_output.write_text(
        json.dumps(robustness_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    passages = {row["passage_id"]: row for row in read_jsonl(args.passages)}
    failures = []
    for query_id, rerank_row in reranker.items():
        if rerank_row["gold_after"] is not None:
            continue
        record = diagnostic[query_id]
        ranked = full_rows[query_id]["ranked_passage_ids"]
        top = passages[ranked[0]] if ranked else None
        if rerank_row["gold_before"] is not None:
            category = "reranker failure"
            cause = (
                "Gold evidence was in the retrieval top 10 but moved below rank 10 after reranking."
            )
        elif top and top["article_id"] == record["gold_article_id"]:
            category = "correct article but wrong passage"
            cause = (
                "The top result came from the gold article but not the annotated evidence passage."
            )
        else:
            category = TYPE_FAILURE[record["query_type"]]
            cause = f"The gold passage was absent from the final top 10 for this {record['query_type']} query."
        failures.append(
            {
                "query_id": query_id,
                "query_type": record["query_type"],
                "roman_urdu_query": record["roman_urdu_query"],
                "gold_passage_id": record["gold_passage_id"],
                "top_retrieved_passage_id": "" if top is None else top["passage_id"],
                "top_retrieved_title": "" if top is None else top["title"],
                "category": category,
                "cause": cause,
                "affected_system": "QueryBridge + BM25 + dense + RRF + reranker",
                "possible_future_improvement": IMPROVEMENTS[category],
                "categorization_status": "rule_assigned_requires_human_review",
            }
        )
    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in failures:
        by_category[row["category"]].append(row)
    selected = []
    while len(selected) < 30 and any(by_category.values()):
        for category in sorted(by_category):
            if by_category[category] and len(selected) < 30:
                selected.append(by_category[category].pop(0))
    args.failures_output.parent.mkdir(parents=True, exist_ok=True)
    with args.failures_output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(selected[0]))
        writer.writeheader()
        writer.writerows(selected)

    ablations = json.loads(args.ablation_report.read_text(encoding="utf-8"))["configurations"]
    args.figures_dir.mkdir(parents=True, exist_ok=True)
    bar_svg(
        "Raabta retrieval ablations — Recall@10",
        list(ablations),
        [ablations[name]["recall_at_10"] for name in ablations],
        args.figures_dir / "ablation_recall_at_10.svg",
    )
    type_names = list(robustness)
    bar_svg(
        "Reranked Raabta robustness — Recall@10",
        type_names,
        [robustness[name]["querybridge_reranked"]["recall_at_10"] for name in type_names],
        args.figures_dir / "robustness_recall_at_10.svg",
    )
    manifest = json.loads(args.embedding_manifest.read_text(encoding="utf-8"))
    baseline_report = json.loads(args.baseline_report.read_text(encoding="utf-8"))
    querybridge_report = json.loads(args.querybridge_report.read_text(encoding="utf-8"))
    reranker_report = json.loads(args.reranker_report.read_text(encoding="utf-8"))
    reranker_benchmark = json.loads(args.reranker_benchmark.read_text(encoding="utf-8"))
    latency = {
        "status": "development_only_project_verified",
        "test_queries_used": 0,
        "index_build_seconds": manifest["build_seconds"],
        "embedding_index_bytes": Path("artifacts/embeddings/e5_small_150_30.npy").stat().st_size,
        "embedding_matrix_shape": manifest["embedding_shape"],
        "query_latency_ms": {
            **{
                name: {
                    "mean": values["mean_latency_ms"],
                    "p95": values["p95_latency_ms"],
                }
                for name, values in baseline_report["systems"].items()
            },
            "querybridge_no_reranker": {
                "mean": querybridge_report["result"]["mean_latency_ms"],
                "p95": querybridge_report["result"]["p95_latency_ms"],
            },
            "reranker_depth20": {"mean": reranker_report["mean_rerank_ms"]},
            "querybridge_plus_reranker_depth20": {
                "mean": round(
                    reranker_report["mean_retrieval_ms"] + reranker_report["mean_rerank_ms"], 3
                )
            },
        },
        "peak_observed_resident_memory_mb": reranker_benchmark[
            "resident_memory_mb_after_benchmark"
        ],
        "answer_generation_latency": "not_measured",
        "notes": [
            "Index build time includes passage embedding generation and NumPy serialization.",
            "Single-transliteration BM25 latency includes deterministic transliteration.",
            "Peak RAM is the observed process resident memory after the cold reranker benchmark.",
        ],
    }
    grounded_smoke_path = Path("reports/tables/grounded_qa_smoke.json")
    if grounded_smoke_path.is_file():
        grounded_smoke = json.loads(grounded_smoke_path.read_text(encoding="utf-8"))
        latency["answer_generation_latency"] = {
            "answer_selection_smoke_ms": grounded_smoke["latency_ms"]["answer_selection"],
            "scope": "one_real_corpus_query_not_an_aggregate",
        }
    args.latency_output.parent.mkdir(parents=True, exist_ok=True)
    args.latency_output.write_text(
        json.dumps(latency, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "development_queries": len(expected),
                "query_types": len(robustness),
                "failure_cases_written": len(selected),
                "failure_categories": {
                    key: sum(row["category"] == key for row in selected)
                    for key in sorted({row["category"] for row in selected})
                },
                "test_queries_used": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
