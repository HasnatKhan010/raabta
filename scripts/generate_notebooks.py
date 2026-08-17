"""Create the seven lightweight, reproducible research notebooks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def markdown(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.splitlines()],
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.splitlines()],
    }


COMMON = """from pathlib import Path
import csv, hashlib, json, random, statistics
from collections import Counter
ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
SEED = 20250816
random.seed(SEED)
print(f"Project: {ROOT.name} | fixed seed: {SEED}")"""


SPECS = {
    "01_dataset_setup.ipynb": (
        "Dataset setup and provenance",
        "Documents the frozen corpus sources, revisions, passage count, and checksums. Downloads are intentionally not triggered from a notebook.",
        """manifest = json.loads((ROOT / "artifacts/metadata/phase1_manifest.json").read_text(encoding="utf-8"))
print(json.dumps(manifest, ensure_ascii=False, indent=2))""",
    ),
    "02_eda_and_preprocessing.ipynb": (
        "EDA and preprocessing",
        "Computes deterministic corpus summaries from the frozen 150/30 passage file and saves the important summary under reports/tables.",
        """rows = [json.loads(line) for line in (ROOT / "data/processed/passages_150_30.jsonl").open(encoding="utf-8")]
domains = {}
for row in rows:
    domains[row["domain"]] = domains.get(row["domain"], 0) + 1
summary = {"passages": len(rows), "mean_tokens": round(statistics.fmean(row["token_count"] for row in rows), 3), "domains": domains}
target = ROOT / "reports/tables/notebook_eda_summary.json"
target.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))""",
    ),
    "03_baseline_retrieval.ipynb": (
        "Frozen retrieval baselines",
        "Displays the three baseline definitions and real development-only measurements. The locked test split is not read.",
        """report = json.loads((ROOT / "reports/tables/provisional_baselines_development.json").read_text(encoding="utf-8"))
assert report["test_queries_used"] == 0
print(json.dumps(report["systems"], indent=2, sort_keys=True))""",
    ),
    "04_querybridge.ipynb": (
        "QueryBridge evaluation",
        "Shows the controlled multi-query development result and the supporting-data lexicon size without using relevance labels during generation.",
        """report = json.loads((ROOT / "reports/tables/provisional_querybridge_development.json").read_text(encoding="utf-8"))
lexicon = json.loads((ROOT / "artifacts/metadata/transliteration_lexicon.json").read_text(encoding="utf-8"))
assert report["test_queries_used"] == 0
print({"lexicon_entries": len(lexicon["entries"]), **report["result"]})""",
    ),
    "05_ablation.ipynb": (
        "Component ablations",
        "Displays the retrieval-stage leave-one-component-out controls. Reranker-retained controls remain pending for the main PC.",
        """report = json.loads((ROOT / "reports/tables/provisional_retrieval_ablations.json").read_text(encoding="utf-8"))
assert report["test_queries_used"] == 0
for name, values in report["configurations"].items():
    print(f"{name:24s} Recall@10={values['recall_at_10']:.4f} MRR@10={values['mrr_at_10']:.4f}")""",
    ),
    "06_robustness.ipynb": (
        "Robustness by query type",
        "Compares the reranked Raabta result across all eight frozen development query categories.",
        """report = json.loads((ROOT / "reports/tables/provisional_robustness.json").read_text(encoding="utf-8"))
assert report["test_queries_used"] == 0
for name, systems in report["query_types"].items():
    values = systems["querybridge_reranked"]
    print(f"{name:30s} n={values['queries']:2d} Recall@10={values['recall_at_10']:.4f}")""",
    ),
    "07_error_analysis.ipynb": (
        "Provisional error analysis",
        "Summarizes the 30 traceable rule-assigned failures. Native-speaker review is required before paper claims.",
        """with (ROOT / "reports/error_analysis/provisional_failures_30.csv").open(encoding="utf-8-sig", newline="") as handle:
    failures = list(csv.DictReader(handle))
categories = {}
for row in failures:
    categories[row["category"]] = categories.get(row["category"], 0) + 1
assert len(failures) >= 30
print(json.dumps({"failures": len(failures), "categories": categories, "review_status": "human review pending"}, ensure_ascii=False, indent=2))""",
    ),
}

# Additional analyses turn the notebooks into reproducible investigations rather
# than simple report viewers.  All inputs are frozen local files.
EXTRA_ANALYSES = {
    "01_dataset_setup.ipynb": [
        ("Artifact integrity", "manifest = json.loads((ROOT / 'artifacts/metadata/phase1_manifest.json').read_text(encoding='utf-8'))\nchecks = []\nfor item in manifest['passage_variants']:\n    path = ROOT / item['path']\n    digest = hashlib.sha256(path.read_bytes()).hexdigest()\n    checks.append({'file': path.name, 'expected_passages': item['passages'], 'actual_passages': sum(1 for line in path.open(encoding='utf-8') if line.strip()), 'checksum_ok': digest == item['sha256']})\nprint(json.dumps(checks, indent=2))\nassert all(row['expected_passages'] == row['actual_passages'] and row['checksum_ok'] for row in checks)"),
        ("Diagnostic split audit", "with (ROOT / 'data/diagnostic/raabta_diagnostic_codex.csv').open(encoding='utf-8-sig', newline='') as handle:\n    rows = list(csv.DictReader(handle))\nprint('Questions:', len(rows))\nprint('Split:', dict(Counter(row['split'] for row in rows)))\nprint('Query types:', dict(sorted(Counter(row['query_type'] for row in rows).items())))\nassert Counter(row['split'] for row in rows) == {'development': 120, 'test': 60}"),
    ],
    "02_eda_and_preprocessing.ipynb": [
        ("Article and passage distributions", "articles = [json.loads(line) for line in (ROOT / 'data/raw/wikipedia.jsonl').open(encoding='utf-8') if line.strip()]\npassages = [json.loads(line) for line in (ROOT / 'data/processed/passages_150_30.jsonl').open(encoding='utf-8') if line.strip()]\nprint('Article domains:', dict(sorted(Counter(row['domain'] for row in articles).items())))\nprint('Passage domains:', dict(sorted(Counter(row['domain'] for row in passages).items())))\ntokens = [row['token_count'] for row in passages]\nprint({'min': min(tokens), 'median': statistics.median(tokens), 'mean': round(statistics.fmean(tokens), 3), 'max': max(tokens), 'unique_articles': len({row['article_id'] for row in passages})})"),
        ("Chunking comparison", "manifest = json.loads((ROOT / 'artifacts/metadata/phase1_manifest.json').read_text(encoding='utf-8'))\nfor item in manifest['passage_variants']:\n    print(Path(item['path']).name, '| passages=', item['passages'], '| mean_tokens=', item['tokens']['mean'], '| represented_articles=', item['represented_articles'])"),
    ],
    "03_baseline_retrieval.ipynb": [
        ("Comparative metrics", "rows = []\nfor name, values in report['systems'].items():\n    rows.append({'system': name, 'R@1': values['recall_at_1'], 'R@5': values['recall_at_5'], 'R@10': values['recall_at_10'], 'MRR@10': values['mrr_at_10'], 'nDCG@10': values['ndcg_at_10']})\nprint(json.dumps(rows, indent=2))"),
        ("Latency trade-off", "for name, values in report['systems'].items():\n    print(name, '| mean_ms=', values['mean_latency_ms'], '| p95_ms=', values['p95_latency_ms'], '| R@10 per 100 ms=', round(values['recall_at_10'] / values['mean_latency_ms'] * 100, 4))\nprint(report['limitation'])"),
    ],
    "04_querybridge.ipynb": [
        ("Improvement over baselines", "baseline = json.loads((ROOT / 'reports/tables/provisional_baselines_development.json').read_text(encoding='utf-8'))\nfor name, values in baseline['systems'].items():\n    print(name, {metric: round(report['result'][metric] - values[metric], 6) for metric in ('recall_at_1', 'recall_at_5', 'recall_at_10', 'mrr_at_10', 'ndcg_at_10')})"),
        ("Lexicon coverage", "lexicon = json.loads((ROOT / 'artifacts/metadata/transliteration_lexicon.json').read_text(encoding='utf-8'))['entries']\nwith (ROOT / 'data/diagnostic/raabta_diagnostic_codex.csv').open(encoding='utf-8-sig', newline='') as handle:\n    development = [row for row in csv.DictReader(handle) if row['split'] == 'development']\nimport re\ncoverage = []\nfor row in development:\n    tokens = re.findall(r'[a-z0-9]+', row['roman_urdu_query'].lower())\n    coverage.append(sum(token in lexicon for token in tokens) / len(tokens) if tokens else 0)\nprint({'lexicon_entries': len(lexicon), 'mean_token_coverage': round(statistics.fmean(coverage), 4), 'full_coverage_queries': sum(value == 1 for value in coverage)})"),
    ],
    "05_ablation.ipynb": [
        ("Deltas from full system", "full = report['configurations']['full_no_reranker']\ndeltas = []\nfor name, values in report['configurations'].items():\n    if name != 'full_no_reranker':\n        deltas.append({'removed': name.removeprefix('no_'), 'delta_R@10': round(values['recall_at_10'] - full['recall_at_10'], 6), 'delta_MRR@10': round(values['mrr_at_10'] - full['mrr_at_10'], 6), 'latency_delta_ms': round(values['mean_latency_ms'] - full['mean_latency_ms'], 3)})\nprint(json.dumps(sorted(deltas, key=lambda row: row['delta_R@10']), indent=2))"),
        ("Ablation interpretation", "worst = min(deltas, key=lambda row: row['delta_R@10'])\nbest_mrr = max(report['configurations'].items(), key=lambda item: item[1]['mrr_at_10'])\nprint('Largest Recall@10 loss:', worst)\nprint('Highest MRR@10 configuration:', best_mrr[0], best_mrr[1]['mrr_at_10'])\nprint(report['limitation'])"),
    ],
    "06_robustness.ipynb": [
        ("Per-query-type comparison", "rows = []\nfor query_type, systems in sorted(report['query_types'].items()):\n    direct = systems['direct_dense']; bridge = systems['querybridge_no_reranker']; reranked = systems['querybridge_reranked']\n    rows.append({'query_type': query_type, 'n': direct['queries'], 'direct_R@10': direct['recall_at_10'], 'bridge_R@10': bridge['recall_at_10'], 'reranked_R@10': reranked['recall_at_10'], 'bridge_delta': round(bridge['recall_at_10'] - direct['recall_at_10'], 6)})\nprint(json.dumps(rows, indent=2))"),
        ("Weighted summary", "total = sum(row['n'] for row in rows)\nprint({'weighted_direct_R@10': round(sum(row['n'] * row['direct_R@10'] for row in rows) / total, 6), 'weighted_bridge_R@10': round(sum(row['n'] * row['bridge_R@10'] for row in rows) / total, 6), 'weakest_reranked_types': [row['query_type'] for row in sorted(rows, key=lambda row: row['reranked_R@10'])[:3]]})"),
    ],
    "07_error_analysis.ipynb": [
        ("Failure-category distribution", "categories = Counter(row['category'] for row in failures)\nprint({'failures': len(failures), 'categories': dict(categories), 'query_types': dict(Counter(row['query_type'] for row in failures))})\nassert all(row['gold_passage_id'] and row['top_retrieved_passage_id'] for row in failures)"),
        ("Traceable examples", "for category in sorted(categories):\n    row = next(item for item in failures if item['category'] == category)\n    print({'category': category, 'query_id': row['query_id'], 'query': row['roman_urdu_query'], 'gold': row['gold_passage_id'], 'retrieved': row['top_retrieved_passage_id'], 'hypothesis': row['possible_future_improvement']})\nprint('Improvement fields are hypotheses; they are not measured fixes.')"),
    ],
}


def main() -> None:
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    for filename, (title, purpose, analysis) in SPECS.items():
        notebook = {
            "cells": [
                markdown(
                    f"# {title}\n\n{purpose}\n\n**Status:** provisional development evidence; zero locked test queries used."
                ),
                code(COMMON),
                code(analysis),
                *[
                    cell
                    for heading, source in EXTRA_ANALYSES.get(filename, [])
                    for cell in (markdown(f"## {heading}"), code(source))
                ],
                markdown(
                    "## Interpretation\n\nOutputs above are measurements from frozen local artifacts. Important limitations must remain attached when reused in the report or viva."
                ),
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Raabta (.venv)",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {"name": "python", "version": "3.11+"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        (NOTEBOOKS / filename).write_text(
            json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(filename)


if __name__ == "__main__":
    main()
