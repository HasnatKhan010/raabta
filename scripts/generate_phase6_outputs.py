"""Regenerate Phase 6 tables and SVG figures from measured development artifacts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REQUIRED = (
    "work/baseline_development_details.jsonl",
    "work/ablation_development_details.jsonl",
    "work/reranker_depth20_checkpoint.jsonl",
    "reports/tables/provisional_retrieval_ablations.json",
)


def main() -> None:
    missing = [path for path in REQUIRED if not Path(path).is_file()]
    if missing:
        raise SystemExit("Missing measured Phase 2/5/6 inputs: " + ", ".join(missing))
    environment = {**os.environ, "PYTHONPATH": "src", "PYTHONUTF8": "1"}
    command = [
        sys.executable,
        "scripts/analyze_phase6.py",
        "--diagnostic",
        "data/diagnostic/raabta_diagnostic_codex.csv",
        "--passages",
        "data/processed/passages_150_30.jsonl",
        "--baseline-details",
        "work/baseline_development_details.jsonl",
        "--ablation-details",
        "work/ablation_development_details.jsonl",
        "--ablation-report",
        "reports/tables/provisional_retrieval_ablations.json",
        "--reranker-checkpoint",
        "work/reranker_depth20_checkpoint.jsonl",
        "--robustness-output",
        "reports/tables/provisional_robustness.json",
        "--failures-output",
        "reports/error_analysis/provisional_failures_30.csv",
        "--figures-dir",
        "reports/figures",
        "--latency-output",
        "reports/tables/provisional_latency_resources.json",
        "--embedding-manifest",
        "artifacts/metadata/e5_small_150_30.json",
        "--baseline-report",
        "reports/tables/provisional_baselines_development.json",
        "--querybridge-report",
        "reports/tables/provisional_querybridge_development.json",
        "--reranker-report",
        "reports/tables/provisional_reranker_depth20.json",
        "--reranker-benchmark",
        "reports/tables/reranker_cpu_benchmark.json",
    ]
    subprocess.run(command, check=True, env=environment)


if __name__ == "__main__":
    main()
