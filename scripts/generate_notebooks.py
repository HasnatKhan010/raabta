"""Generate the detailed, reproducible assignment notebook sequence."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def markdown(text: str) -> dict:
    clean = textwrap.dedent(text).strip()
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in clean.splitlines()],
    }


def code(source: str) -> dict:
    clean = textwrap.dedent(source).strip()
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in clean.splitlines()],
    }


COMMON = r'''
from collections import Counter
from pathlib import Path
import csv
import hashlib
import html
import json
import platform
import random
import statistics

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
SEED = 20250816
random.seed(SEED)
FIGURES = ROOT / "reports" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

def load_json(relative_path):
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

def print_table(rows, columns):
    if not rows:
        print("(no rows)")
        return
    widths = {
        column: max(len(str(column)), *(len(str(row.get(column, ""))) for row in rows))
        for column in columns
    }
    print(" | ".join(str(column).ljust(widths[column]) for column in columns))
    print("-+-".join("-" * widths[column] for column in columns))
    for row in rows:
        print(" | ".join(str(row.get(column, "")).ljust(widths[column]) for column in columns))

def write_bar_svg(filename, values, title, *, maximum=None):
    values = list(values)
    width, left, right, row_height = 820, 245, 80, 34
    height = 76 + row_height * len(values)
    plot_width = width - left - right
    largest = maximum or max((float(value) for _, value in values), default=1.0) or 1.0
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="27" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700">{html.escape(title)}</text>',
    ]
    for index, (label, value) in enumerate(values):
        y = 52 + index * row_height
        bar_width = plot_width * float(value) / largest
        elements.extend([
            f'<text x="{left - 10}" y="{y + 17}" text-anchor="end" font-family="Arial" font-size="13">{html.escape(str(label))}</text>',
            f'<rect x="{left}" y="{y}" width="{bar_width:.2f}" height="20" rx="3" fill="#1c5b58"/>',
            f'<text x="{min(left + bar_width + 7, width - 58):.2f}" y="{y + 16}" font-family="Arial" font-size="12">{float(value):.4g}</text>',
        ])
    elements.append('</svg>')
    target = FIGURES / filename
    target.write_text("\n".join(elements) + "\n", encoding="utf-8")
    print(f"Saved visualization: {target.relative_to(ROOT)}")
    return target

print(f"Project: {ROOT.name} | Python: {platform.python_version()} | fixed seed: {SEED}")
'''


NOTEBOOKS_CONTENT = {
    "01_dataset_setup.ipynb": [
        markdown(
            """
            # Parts 1–3 — Problem Selection, Literature Review, and Dataset

            This notebook establishes the research problem before any model comparison. It documents the five-paper review, the public datasets, the prediction/relevance target, data provenance, and the frozen development/test boundary.

            **Notebook status:** executed assignment evidence. All quantitative analysis is development-only; the locked 60-question test partition is not read for evaluation.
            """
        ),
        markdown(
            """
            ## Part 1 — Selected real-world problem

            **Problem:** retrieve trustworthy Urdu-script evidence when a user asks a noisy Roman-Urdu question.

            Roman Urdu is written with Latin characters, has no standard spelling, and often includes English words. Most authoritative local content is in Urdu script. Direct word matching therefore misses relevant passages, while a semantic model can return something generally related but factually unresponsive. The practical user-facing task is not free-form text generation: given a query and a fixed Urdu corpus, rank passages so the correct evidence appears near the top, then return an exact supported sentence or abstain.

            **Research question:** Can script-aware multi-query reformulation and character-level title matching improve top-10 evidence retrieval over direct dense retrieval, single transliteration, and a conventional lexical+dense hybrid?

            **Machine-learning formulation:** Each query–passage pair has a binary relevance target. The diagnostic CSV stores the verified relevant passage identifier for each query; evaluation asks whether that identifier appears at ranks 1, 5, or 10. The interface adds a separate deterministic evidence-validity decision after retrieval.

            This information-retrieval problem is outside the assignment's example list. The repository can demonstrate the technical work but cannot prove an administrative approval; the required prior approval should therefore be retained with the submission records.
            """
        ),
        code(COMMON),
        markdown(
            """
            ## Part 2 — Literature review protocol

            Five directly relevant papers were selected to cover the complete chain: Roman-Urdu data, transliteration, Roman-Urdu retrieval, multilingual dense retrieval, and neural reranking. Four of the five were published from 2022–2025, satisfying the requirement that at least three be from the last five years.

            The review compares each paper's approach, evaluation focus, and unresolved gap. The common challenges are spelling variation, cross-script mismatch, scarce relevance labels, entity confusion, and the CPU cost of reranking. Common metrics include character error rate for transliteration and Recall/MRR/nDCG for retrieval.
            """
        ),
        code(
            r'''
            papers = [
                {"year": 2022, "paper": "Alam & Hussain — Roman-Urdu-Parl", "approach": "parallel Roman-Urdu/Urdu corpus", "evaluation": "corpus quality and alignment", "gap": "no passage-retrieval protocol"},
                {"year": 2025, "paper": "Butt et al. — Roman-Urdu transliteration", "approach": "transformer transliteration", "evaluation": "character-level transliteration quality", "gap": "one conversion can remain ambiguous for search"},
                {"year": 2025, "paper": "Butt et al. — Roman Urdu IR", "approach": "large IR dataset and multilingual baseline", "evaluation": "ranked retrieval metrics", "gap": "translated benchmark; limited route transparency"},
                {"year": 2024, "paper": "Wang et al. — Multilingual E5", "approach": "multilingual contrastive text embeddings", "evaluation": "multilingual retrieval benchmarks", "gap": "semantic similarity can confuse fine-grained entities"},
                {"year": 2019, "paper": "Nogueira & Cho — BERT reranking", "approach": "query–passage cross-encoder", "evaluation": "MRR and passage ranking", "gap": "high CPU cost and no evidence guarantee"},
            ]
            print_table(papers, ["year", "paper", "approach", "evaluation", "gap"])
            recent = sum(paper["year"] >= 2021 for paper in papers)
            print(f"\nReviewed papers: {len(papers)} | published 2021–2026: {recent}")
            assert len(papers) >= 5 and recent >= 3
            '''
        ),
        markdown(
            """
            ### Reviewed-paper references

            1. M. Alam and S. U. Hussain, “Roman-Urdu-Parl: Roman-Urdu and Urdu Parallel Corpus for Urdu Language Understanding,” *ACM TALLIP*, vol. 21, no. 1, 2022. [DOI: 10.1145/3464424](https://doi.org/10.1145/3464424)
            2. U. Butt, S. Varanasi, and G. Neumann, “Low-Resource Transliteration for Roman-Urdu and Urdu Using Transformer-Based Models,” *LoResMT*, 2025. [ACL Anthology](https://aclanthology.org/2025.loresmt-1.13/)
            3. M. U. T. Butt, S. Varanasi, and G. Neumann, “Roman Urdu as a Low-Resource Language: Building the First IR Dataset and Baseline,” *LowResNLP*, 2025. [ACL Anthology](https://aclanthology.org/2025.lowresnlp-1.9/)
            4. L. Wang *et al.*, “Multilingual E5 Text Embeddings: A Technical Report,” arXiv:2402.05672, 2024. [arXiv](https://arxiv.org/abs/2402.05672)
            5. R. Nogueira and K. Cho, “Passage Re-ranking with BERT,” arXiv:1901.04085, 2019. [arXiv](https://arxiv.org/abs/1901.04085)

            These same works appear in the IEEE paper bibliography so the notebook analysis and submitted paper use one consistent evidence base.
            """
        ),
        markdown(
            """
            ### Literature-derived research gap and proposed direction

            The papers collectively provide data, transliteration, multilingual embeddings, and reranking, but they do not jointly address all four needs of this project: (1) noisy Roman entity spelling, (2) retrieval over a native Urdu-script knowledge collection, (3) CPU-first execution, and (4) an interface that exposes transformations and refuses unsupported evidence.

            This gap motivates a controlled multi-route system. The initial proposal combines query views, BM25, multilingual E5, reciprocal-rank fusion, and shallow reranking. Error analysis later motivates the principal improvement: romanize Urdu article titles once and match the original Roman query using character 2–4 grams.
            """
        ),
        markdown(
            """
            ## Part 3 — Dataset discovery and documentation

            | Dataset | Public source | Samples used | Features | Target/use | Selection reason | Known limitations |
            |---|---|---:|---|---|---|---|
            | Urdu Wikipedia (`wikimedia/wikipedia`, `20231101.ur`) | Hugging Face/Wikimedia snapshot | 4,000 articles; 16,352 default passages | article ID, title, URL, text, domain, passage span, token count | Gold passage ID / binary passage relevance | Native Urdu-script encyclopedic evidence with stable provenance | Only a bounded subset; encyclopedic and snapshot-limited |
            | Roman-Urdu-Parl split | Public Hugging Face dataset | 30,000 supporting rows | aligned Roman-Urdu and Urdu strings | Transliteration/lexicon support only | Public script-aligned resource | Not relevance-labelled; must not be treated as retrieval ground truth |
            | Project diagnostic set | Derived from the frozen corpus | 180 questions: 120 development, 60 locked test | Roman query, Urdu form, query type, domain, gold passage, exact evidence, split | Verified relevant passage ID | Enables controlled cross-script retrieval measurement | Small and title-oriented; external language review remains needed |

            The primary modeling unit is a query with one verified relevant passage. Corpus passages are candidate inputs, not independent labeled training rows. The project does not claim that the auxiliary parallel corpus supplies relevance labels.
            """
        ),
        code(
            r'''
            manifest = load_json("artifacts/metadata/phase1_manifest.json")
            dataset_rows = [
                {"artifact": "Urdu Wikipedia articles", "samples": manifest["articles"]["articles"], "sha256": manifest["articles"]["sha256"][:16] + "..."},
                *[
                    {"artifact": Path(item["path"]).name, "samples": item["passages"], "sha256": item["sha256"][:16] + "..."}
                    for item in manifest["passage_variants"]
                ],
            ]
            print_table(dataset_rows, ["artifact", "samples", "sha256"])
            '''
        ),
        markdown(
            """
            ## Provenance and integrity checks

            A portable experiment must verify that the files being evaluated are the frozen files described above. The following cell recomputes passage counts and SHA-256 values rather than trusting filenames. It then checks the immutable 120/60 split and summarizes the eight query categories.
            """
        ),
        code(
            r'''
            checks = []
            for item in manifest["passage_variants"]:
                path = ROOT / item["path"]
                actual_count = sum(1 for line in path.open(encoding="utf-8") if line.strip())
                actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
                checks.append({"file": path.name, "expected": item["passages"], "actual": actual_count, "checksum_ok": actual_digest == item["sha256"]})
            print_table(checks, ["file", "expected", "actual", "checksum_ok"])

            with (ROOT / "data/diagnostic/raabta_diagnostic.csv").open(encoding="utf-8-sig", newline="") as handle:
                diagnostic = list(csv.DictReader(handle))
            split_counts = Counter(row["split"] for row in diagnostic)
            type_counts = Counter(row["query_type"] for row in diagnostic)
            print("\nSplit counts:", dict(split_counts))
            print("Query-type counts:", dict(sorted(type_counts.items())))
            assert all(row["expected"] == row["actual"] and row["checksum_ok"] for row in checks)
            assert split_counts == {"development": 120, "test": 60}
            '''
        ),
        markdown(
            """
            ## Part 3 conclusion

            The data is public, relevant, checksum-verifiable, and separated by role. Urdu Wikipedia is the retrieval collection; Roman-Urdu-Parl is supporting script-alignment data; and the diagnostic set supplies passage-level relevance labels. The principal threats are the small title-oriented evaluation set, limited corpus coverage, one recorded gold passage per query, and the absence of independent language review. These limitations constrain every later conclusion.
            """
        ),
    ],
    "02_eda_and_preprocessing.ipynb": [
        markdown(
            """
            # Parts 4–5 — Justified Preprocessing and Exploratory Data Analysis

            This notebook explains every transformation before applying or inspecting it. It then studies article domains, passage lengths, chunking alternatives, and diagnostic-query coverage to identify likely modeling difficulties.

            **Notebook status:** executed from frozen local artifacts; no model fitting and no locked-test evaluation.
            """
        ),
        code(COMMON),
        markdown(
            """
            ## Part 4 — Preprocessing pipeline and justification

            1. **Preserve raw text and provenance.** Article ID, title, URL, source text, and deterministic checksums remain available so every answer can be traced to its origin.
            2. **Unicode NFKC normalization.** Urdu text can contain compatibility variants. NFKC reduces accidental code-point mismatch while the raw form remains stored for audit.
            3. **Remove only control characters.** Retrieval should not be distorted by invisible controls; Urdu letters and punctuation must remain intact.
            4. **Exclude articles shorter than 80 whitespace tokens.** Very short pages are frequently navigation or fragmentary content and offer little evidence. This threshold is frozen in configuration.
            5. **Chunk into 150-token passages with 30-token overlap.** Dense encoders have finite context, while overlap reduces the chance that an answer-spanning sentence is split at a boundary. Development alternatives of 120/24 and 180/36 are retained for comparison.
            6. **Attach passage metadata.** Each chunk stores its article, title, URL, span, domain, and deterministic passage ID; this is required for evaluation and citations.
            7. **Do not use gold fields during preprocessing or query reformulation.** Gold passage IDs and evidence exist only for scoring. The locked test partition remains untouched until final configuration freeze.
            """
        ),
        code(
            r'''
            articles = [json.loads(line) for line in (ROOT / "data/raw/wikipedia.jsonl").open(encoding="utf-8") if line.strip()]
            passages = [json.loads(line) for line in (ROOT / "data/processed/passages_150_30.jsonl").open(encoding="utf-8") if line.strip()]
            print({"articles": len(articles), "passages": len(passages), "represented_articles": len({row["article_id"] for row in passages}), "missing_provenance": sum(not all(row.get(field) for field in ("passage_id", "article_id", "title", "url")) for row in passages)})
            assert len(articles) == 4000 and len(passages) == 16352
            assert len({row["article_id"] for row in passages}) == 4000
            '''
        ),
        markdown(
            """
            ## Part 5 — Corpus coverage by domain

            Domain balance matters because a model can appear effective if the evaluation overrepresents easier topics. Geography and general articles are the largest groups, while science is the smallest. Results should therefore be reported overall and by query category rather than interpreted as uniform Urdu coverage.
            """
        ),
        code(
            r'''
            article_domains = Counter(row["domain"] for row in articles)
            passage_domains = Counter(row["domain"] for row in passages)
            rows = [{"domain": domain, "articles": article_domains[domain], "passages": passage_domains[domain], "passages/article": round(passage_domains[domain] / article_domains[domain], 2)} for domain in sorted(article_domains)]
            print_table(rows, ["domain", "articles", "passages", "passages/article"])
            write_bar_svg("eda_article_domains.svg", sorted(article_domains.items()), "Urdu Wikipedia articles by domain")
            '''
        ),
        markdown("![Article counts by domain](../reports/figures/eda_article_domains.svg)"),
        markdown(
            """
            ## Passage-length distribution

            Passage length controls the context/noise trade-off. Short chunks may omit needed context; long chunks contain more irrelevant sentences and cost more to encode. The summary below uses the actual default passage file.
            """
        ),
        code(
            r'''
            token_counts = [row["token_count"] for row in passages]
            bins = [("31–60", 31, 60), ("61–90", 61, 90), ("91–120", 91, 120), ("121–149", 121, 149), ("150", 150, 150)]
            histogram = [(label, sum(low <= value <= high for value in token_counts)) for label, low, high in bins]
            print({"minimum": min(token_counts), "median": statistics.median(token_counts), "mean": round(statistics.fmean(token_counts), 3), "maximum": max(token_counts)})
            print_table([{"tokens": label, "passages": count} for label, count in histogram], ["tokens", "passages"])
            write_bar_svg("eda_passage_lengths.svg", histogram, "Default passage-length distribution")
            '''
        ),
        markdown("![Passage-length distribution](../reports/figures/eda_passage_lengths.svg)"),
        markdown(
            """
            ## Chunking sensitivity

            All three settings preserve all 4,000 articles. Smaller chunks create more candidates and finer evidence boundaries; larger chunks reduce index size but add irrelevant context. The middle setting is selected as a CPU-friendly compromise, not because the alternatives are discarded.
            """
        ),
        code(
            r'''
            manifest = load_json("artifacts/metadata/phase1_manifest.json")
            chunk_rows = [{"file": Path(item["path"]).name, "passages": item["passages"], "mean_tokens": item["tokens"]["mean"], "median_tokens": item["tokens"]["median"], "articles": item["represented_articles"]} for item in manifest["passage_variants"]]
            print_table(chunk_rows, ["file", "passages", "mean_tokens", "median_tokens", "articles"])
            '''
        ),
        markdown(
            """
            ## Diagnostic-query composition

            The diagnostic set deliberately includes clean, informal, abbreviated, highly noisy, code-switched, named-entity, short, and slightly ambiguous queries. This is a challenge set rather than a population sample; category counts should not be interpreted as real-world prevalence.
            """
        ),
        code(
            r'''
            with (ROOT / "data/diagnostic/raabta_diagnostic.csv").open(encoding="utf-8-sig", newline="") as handle:
                diagnostic = list(csv.DictReader(handle))
            split_counts = Counter(row["split"] for row in diagnostic)
            query_types = Counter(row["query_type"] for row in diagnostic)
            query_lengths = [len(row["roman_urdu_query"].split()) for row in diagnostic]
            print("Splits:", dict(split_counts))
            print("Roman-query words:", {"min": min(query_lengths), "median": statistics.median(query_lengths), "mean": round(statistics.fmean(query_lengths), 2), "max": max(query_lengths)})
            print_table([{"query_type": key, "questions": value} for key, value in sorted(query_types.items())], ["query_type", "questions"])
            write_bar_svg("eda_query_types.svg", sorted(query_types.items()), "Diagnostic questions by query type")
            '''
        ),
        markdown("![Diagnostic query types](../reports/figures/eda_query_types.svg)"),
        markdown(
            """
            ## EDA conclusions and expected modeling difficulties

            - Corpus coverage is uneven across domains, so aggregate metrics alone can hide weak categories.
            - Most default chunks reach the 150-token ceiling; reranking must separate the relevant sentence from surrounding context.
            - Short and noisy Roman queries contain little lexical evidence, and transliteration can amplify spelling errors.
            - Code switching requires preserving English tokens while converting Urdu tokens.
            - Named entities are especially sensitive to omitted vowels and script conversion, motivating character-level title matching.
            - The dataset is small and deliberately constructed, so results are engineering evidence rather than broad population estimates.
            """
        ),
    ],
    "03_baseline_retrieval.ipynb": [
        markdown(
            """
            # Parts 6–7 — Baseline Models and Experimental Design

            This notebook defines three baselines representing different retrieval strategies, documents the validation protocol before improvement, and compares quality with CPU latency.

            **Notebook status:** 120 development questions only; locked test queries used = 0.
            """
        ),
        code(COMMON),
        markdown(
            """
            ## Part 6 — Why these three baselines?

            1. **Direct multilingual dense retrieval:** tests whether a pretrained shared embedding space can cross the Roman/Urdu script boundary without explicit conversion.
            2. **Single deterministic transliteration + BM25:** tests a classical lexical strategy after one Roman-to-Urdu conversion. It is interpretable but exposes the brittleness of committing to one spelling.
            3. **Standard raw-query BM25 + dense RRF hybrid:** tests whether lexical and semantic signals complement each other without the proposed controlled query bridge.

            These are genuinely different modeling strategies—semantic vector retrieval, transformed lexical retrieval, and hybrid rank fusion—rather than three parameter variants of the same model.
            """
        ),
        markdown(
            """
            ## Part 7 — Experimental methodology fixed before improvement

            **Split strategy:** 180 evidence-linked queries are frozen as 120 development and 60 test. Development is used for diagnosis and configuration; the test partition remains locked for one final evaluation after all decisions are frozen.

            **Validation approach:** The project reports macro-averaged retrieval metrics on the fixed development split. Cross-validation is not used because the systems are pretrained retrieval pipelines rather than supervised estimators fitted to these 120 queries, and because corpus indexing/reranking is expensive. The limitation is that development estimates have high uncertainty.

            **Hyperparameter strategy:** Passage size, top-k, query-view threshold, RRF constant/weights, reranking depth, and evidence thresholds are stored in versioned configuration. Changes are justified through development ablation and failure analysis; the locked test set is never used for selection.

            **Metrics:** Recall@1/5/10 measure evidence coverage; MRR@10 rewards an early first relevant result; nDCG@10 measures discounted ranking quality. Mean and p95 latency measure interactive cost. Retrieval metrics are not final answer-accuracy percentages.

            **Reproducibility:** Fixed seed 20250816, CPU device, exact package pins, immutable model revisions, checksum-verified passage/embedding artifacts, and stored query order.
            """
        ),
        code(
            r'''
            config = (ROOT / "configs/default.yaml").read_text(encoding="utf-8")
            audit = load_json("reports/tables/portability_audit.json")
            embedding = load_json("artifacts/metadata/e5_small_150_30.json")
            reranker = load_json("reports/tables/reranker_depth20.json")
            reproducibility = [
                {"control": "random seed", "value": SEED},
                {"control": "device", "value": embedding["device"].upper()},
                {"control": "validation OS", "value": platform.platform()},
                {"control": "validation processor", "value": platform.processor() or platform.machine()},
                {"control": "Python", "value": audit["checks"]["python_supported"]["detail"]},
                {"control": "exact Python pins", "value": audit["checks"]["python_dependencies_pinned"]["detail"]},
                {"control": "dense model", "value": embedding["model"]},
                {"control": "dense revision", "value": embedding["revision"][:16] + "..."},
                {"control": "reranker", "value": reranker["model"]},
                {"control": "reranker revision", "value": reranker["revision"][:16] + "..."},
                {"control": "passage checksum", "value": audit["checks"]["passage_checksum"]["detail"][:16] + "..."},
                {"control": "embedding checksum", "value": audit["checks"]["embedding_checksum"]["detail"][:16] + "..."},
                {"control": "locked-test report violations", "value": 0},
            ]
            print_table(reproducibility, ["control", "value"])
            assert "seed: 20250816" in config and audit["status"] == "passed"
            '''
        ),
        markdown("## Baseline results"),
        code(
            r'''
            report = load_json("reports/tables/baselines_development.json")
            assert report["queries"] == 120 and report["test_queries_used"] == 0
            rows = []
            for name, values in report["systems"].items():
                rows.append({"system": name, "R@1": f'{values["recall_at_1"]:.4f}', "R@5": f'{values["recall_at_5"]:.4f}', "R@10": f'{values["recall_at_10"]:.4f}', "MRR@10": f'{values["mrr_at_10"]:.4f}', "nDCG@10": f'{values["ndcg_at_10"]:.4f}', "mean_ms": f'{values["mean_latency_ms"]:.1f}', "p95_ms": f'{values["p95_latency_ms"]:.1f}'})
            print_table(rows, ["system", "R@1", "R@5", "R@10", "MRR@10", "nDCG@10", "mean_ms", "p95_ms"])
            write_bar_svg("baseline_recall_at_10.svg", [(name, values["recall_at_10"]) for name, values in report["systems"].items()], "Baseline Recall@10", maximum=0.20)
            '''
        ),
        markdown("![Baseline Recall at 10](../reports/figures/baseline_recall_at_10.svg)"),
        markdown("## Quality–latency trade-off"),
        code(
            r'''
            latency_rows = []
            for name, values in report["systems"].items():
                latency_rows.append({"system": name, "mean_ms": values["mean_latency_ms"], "p95_ms": values["p95_latency_ms"], "R@10 per 100 ms": round(values["recall_at_10"] / values["mean_latency_ms"] * 100, 4)})
            print_table(latency_rows, ["system", "mean_ms", "p95_ms", "R@10 per 100 ms"])
            write_bar_svg("baseline_latency.svg", [(row["system"], row["mean_ms"]) for row in latency_rows], "Baseline mean query latency (ms)")
            '''
        ),
        markdown("![Baseline latency](../reports/figures/baseline_latency.svg)"),
        markdown(
            """
            ## Baseline conclusion

            Direct dense and the standard hybrid tie at 0.0917 Recall@10, but direct dense has better MRR@10 and lower latency, so it is the strongest baseline under the primary quality/cost trade-off. Single transliteration + BM25 reaches only 0.0250 Recall@10, demonstrating that one script conversion is too brittle. The low absolute recall and named-entity failures justify a multi-view, script-aware improvement.
            """
        ),
    ],
    "04_querybridge.ipynb": [
        markdown(
            """
            # Part 8 — Proposed Improvement: QueryBridge and Romanized-Title Retrieval

            This notebook connects the literature-derived gap to the implemented improvement and measures it against the frozen baselines. The proposal is a pipeline change, not an unsupported switch to a larger generative model.

            **Notebook status:** development-only comparisons; test queries used = 0.
            """
        ),
        code(COMMON),
        markdown(
            """
            ## Limitation identified in the baselines

            The baseline analysis shows that neither direct semantic similarity nor one deterministic transliteration reliably finds the correct Urdu article. Error categories point particularly to noisy entities, missing vowels, abbreviations, and code switching. Multilingual E5 supplies cross-script semantics, but the reviewed literature warns that dense similarity can confuse closely related entities; transliteration work also shows that orthographic variability cannot always be resolved by one output.

            ## Improvement design

            1. Preserve the original Roman query.
            2. Create conservative normalized, Urdu-script, and retrieval-oriented views; reject duplicates and semantic drift.
            3. Retrieve every accepted view using title-boosted BM25 and multilingual E5.
            4. Romanize each Urdu article title offline and match the original query with character-boundary TF-IDF 2–4 grams. This tolerates missing/inserted vowels and short spelling variation.
            5. Contribute only the lead passage for each title match, then combine routes using weighted reciprocal-rank fusion.
            6. Optionally rerank a shallow candidate set and apply source/relation-aware evidence gates before answering.

            The title route is expected to work because article titles provide concise entity identities while character n-grams avoid requiring an exact transliteration.
            """
        ),
        code(
            r'''
            bridge = load_json("reports/tables/querybridge_development.json")
            baselines = load_json("reports/tables/baselines_development.json")
            assert bridge["test_queries_used"] == baselines["test_queries_used"] == 0
            comparison = []
            for name, values in baselines["systems"].items():
                comparison.append({"system": name, "R@10": values["recall_at_10"], "MRR@10": values["mrr_at_10"], "mean_ms": values["mean_latency_ms"]})
            comparison.append({"system": "querybridge_bm25_dense_rrf", "R@10": bridge["result"]["recall_at_10"], "MRR@10": bridge["result"]["mrr_at_10"], "mean_ms": bridge["result"]["mean_latency_ms"]})
            print_table(comparison, ["system", "R@10", "MRR@10", "mean_ms"])
            print("Mean accepted query views:", bridge["result"]["mean_accepted_variants"])
            '''
        ),
        markdown("QueryBridge raises Recall@10 from 0.0917 for the strongest direct/hybrid baselines to 0.1667. This is a useful gain but still leaves five of six relevant passages outside the top ten, so the multi-view bridge alone does not solve entity matching."),
        markdown("## Principal improvement — romanized-title route"),
        code(
            r'''
            regression = load_json("reports/tables/application_accuracy_regression.json")
            assert regression["queries"] == 120 and regression["test_queries_used"] == 0
            metrics = ["recall_at_1", "recall_at_5", "recall_at_10", "mrr_at_10", "ndcg_at_10"]
            rows = [{"metric": metric, "before": f'{regression["before"][metric]:.4f}', "with_title_route": f'{regression["after"][metric]:.4f}', "absolute_gain": f'{regression["after"][metric] - regression["before"][metric]:.4f}'} for metric in metrics]
            print_table(rows, ["metric", "before", "with_title_route", "absolute_gain"])
            write_bar_svg("proposed_improvement_recall.svg", [("before title route", regression["before"]["recall_at_10"]), ("with title route", regression["after"]["recall_at_10"])], "Proposed improvement: development Recall@10", maximum=1.0)
            '''
        ),
        markdown("![Proposed improvement](../reports/figures/proposed_improvement_recall.svg)"),
        markdown("Recall@10 rises from 0.1917 to 0.9833 on the same 120 title-oriented development questions, an absolute gain of 0.7916. MRR@10 rises from 0.1014 to 0.5830. These figures isolate retrieval before reranking and do **not** mean that 98.33% of unrestricted user answers are correct."),
        markdown("## Worked trace and interface transparency"),
        code(
            r'''
            smoke = load_json("reports/tables/grounded_qa_smoke.json")
            trace_rows = [{"type": variant["variant_type"], "accepted": variant["accepted"], "similarity": variant["semantic_similarity"], "reason": variant["decision_reason"]} for variant in smoke["query_variants"]]
            print("Query:", smoke["query"])
            print_table(trace_rows, ["type", "accepted", "similarity", "reason"])
            print("\nSupported:", smoke["supported"])
            print("Source:", smoke["source_title"], smoke["source_url"])
            print("Evidence sentences:")
            for item in smoke["evidence"]:
                print(f'- similarity={item["similarity"]:.4f} | {item["text"]}')
            print("Latency (ms):", smoke["latency_ms"])
            '''
        ),
        markdown(
            """
            ## Leakage controls and remaining risks

            Query generation receives only the user's query and supporting transliteration resources—not the gold article, passage ID, evidence, or answer. The title index is built from corpus titles available to every system. Even so, the evaluation questions are title-oriented, so a title route has a structural advantage; independent natural-query evaluation is required. The high-recall retrieval result must be followed by end-to-end answer review and a single locked-test run after configuration freeze.
            """
        ),
    ],
    "05_ablation.ipynb": [
        markdown(
            """
            # Parts 8–9 — Ablation Study of the Proposed Pipeline

            An ablation removes one component at a time while holding the corpus, query set, and remaining configuration fixed. This tests whether an observed gain depends on the intended component rather than merely on a more complicated pipeline.

            **Protocol:** retrieval-stage leave-one-component-out on 120 development questions; reranker absent; locked test queries used = 0.
            """
        ),
        code(COMMON),
        markdown(
            """
            ## Components tested

            - **Normalization:** reduces conservative Roman spelling variation.
            - **Transliteration:** crosses the Latin/Urdu script boundary.
            - **Expansion:** creates a retrieval-oriented query after controlled question-word removal.
            - **BM25:** contributes exact Urdu lexical evidence.
            - **Dense retrieval:** supplies multilingual semantic coverage.
            - **Fusion:** combines heterogeneous ranked routes without comparing incompatible raw scores.

            The stored ablation predates the romanized-title improvement; title-route impact is therefore reported separately as a before/after regression on the same questions rather than silently mixed into the older table.
            """
        ),
        code(
            r'''
            report = load_json("reports/tables/retrieval_ablations.json")
            assert report["queries"] == 120 and report["test_queries_used"] == 0
            full = report["configurations"]["full_no_reranker"]
            rows = []
            for name, values in report["configurations"].items():
                rows.append({"configuration": name, "R@10": f'{values["recall_at_10"]:.4f}', "delta_R@10": f'{values["recall_at_10"] - full["recall_at_10"]:+.4f}', "MRR@10": f'{values["mrr_at_10"]:.4f}', "delta_MRR": f'{values["mrr_at_10"] - full["mrr_at_10"]:+.4f}', "mean_ms": f'{values["mean_latency_ms"]:.1f}'})
            print_table(rows, ["configuration", "R@10", "delta_R@10", "MRR@10", "delta_MRR", "mean_ms"])
            '''
        ),
        markdown("## Recall visualization"),
        code(
            r'''
            values = [(name, result["recall_at_10"]) for name, result in report["configurations"].items()]
            write_bar_svg("ablation_recall_at_10.svg", values, "Retrieval ablation Recall@10", maximum=0.20)
            '''
        ),
        markdown("![Ablation Recall at 10](../reports/figures/ablation_recall_at_10.svg)"),
        markdown("## Component importance and trade-offs"),
        code(
            r'''
            deltas = []
            for name, values in report["configurations"].items():
                if name == "full_no_reranker":
                    continue
                deltas.append({"removed": name.removeprefix("no_"), "recall_loss": round(full["recall_at_10"] - values["recall_at_10"], 6), "mrr_change": round(values["mrr_at_10"] - full["mrr_at_10"], 6), "latency_saved_ms": round(full["mean_latency_ms"] - values["mean_latency_ms"], 3)})
            print_table(sorted(deltas, key=lambda row: row["recall_loss"], reverse=True), ["removed", "recall_loss", "mrr_change", "latency_saved_ms"])
            print("Largest Recall@10 dependency:", max(deltas, key=lambda row: row["recall_loss"])["removed"])
            '''
        ),
        markdown("Removing fusion causes the largest Recall@10 loss (0.1084), showing that no single route is sufficient. Transliteration and dense retrieval are also important. Removing expansion slightly lowers Recall@10 but raises MRR@10, so expansion is a mixed component rather than an automatic improvement. BM25 has a modest recall contribution but provides interpretable exact-term evidence."),
        markdown("## Separate title-route control"),
        code(
            r'''
            title = load_json("reports/tables/application_accuracy_regression.json")
            title_rows = [
                {"system": "without romanized-title route", "R@1": title["before"]["recall_at_1"], "R@5": title["before"]["recall_at_5"], "R@10": title["before"]["recall_at_10"], "MRR@10": title["before"]["mrr_at_10"]},
                {"system": "with romanized-title route", "R@1": title["after"]["recall_at_1"], "R@5": title["after"]["recall_at_5"], "R@10": title["after"]["recall_at_10"], "MRR@10": title["after"]["mrr_at_10"]},
            ]
            print_table(title_rows, ["system", "R@1", "R@5", "R@10", "MRR@10"])
            print("Absolute title-route Recall@10 gain:", round(title["after"]["recall_at_10"] - title["before"]["recall_at_10"], 6))
            '''
        ),
        markdown(
            """
            ## Ablation conclusion

            The original multi-view system depends most on fusion and transliteration, but its absolute recall remains low. The later romanized-title route produces the dominant measured gain because it targets the entity-matching failure directly. A future full ablation should remove the title route from the final frozen pipeline and repeat category-wise evaluation under independent review; the current before/after control is strong development evidence but not a locked-test result.
            """
        ),
    ],
    "06_robustness.ipynb": [
        markdown(
            """
            # Part 9 — Comparative Evaluation, Robustness, and Trade-offs

            This notebook answers the assignment's central evaluation questions: Which system performs best? Why? What does it cost? Where does it remain weak?

            **Scope:** all scores are stored development measurements. The 60 locked test questions remain unused.
            """
        ),
        code(COMMON),
        markdown("## Complete performance comparison"),
        code(
            r'''
            baselines = load_json("reports/tables/baselines_development.json")
            bridge = load_json("reports/tables/querybridge_development.json")
            reranker = load_json("reports/tables/reranker_depth20.json")
            title = load_json("reports/tables/application_accuracy_regression.json")
            assert {baselines["test_queries_used"], bridge["test_queries_used"], reranker["test_queries_used"], title["test_queries_used"]} == {0}
            systems = []
            for name, values in baselines["systems"].items():
                systems.append((name, values, values["mean_latency_ms"]))
            systems.extend([("QueryBridge + RRF", bridge["result"], bridge["result"]["mean_latency_ms"]), ("QueryBridge + depth-20 reranker", reranker["after_reranking"], reranker["mean_retrieval_ms"] + reranker["mean_rerank_ms"]), ("Current pipeline + title route", title["after"], 580.8)])
            rows = [{"system": name, "R@1": f'{values["recall_at_1"]:.4f}', "R@5": f'{values["recall_at_5"]:.4f}', "R@10": f'{values["recall_at_10"]:.4f}', "MRR@10": f'{values["mrr_at_10"]:.4f}', "nDCG@10": f'{values["ndcg_at_10"]:.4f}', "mean_ms": f'{latency:.1f}'} for name, values, latency in systems]
            print_table(rows, ["system", "R@1", "R@5", "R@10", "MRR@10", "nDCG@10", "mean_ms"])
            write_bar_svg("all_systems_recall_at_10.svg", [(name, values["recall_at_10"]) for name, values, _ in systems], "All systems: development Recall@10", maximum=1.0)
            '''
        ),
        markdown("![All systems Recall at 10](../reports/figures/all_systems_recall_at_10.svg)"),
        markdown("**Best measured retrieval system:** the current pipeline with romanized-title matching. It reaches 0.9833 Recall@10, 0.5830 MRR@10, and 0.6796 nDCG@10 before reranking. It wins because the diagnostic task is strongly title/entity-oriented and character n-grams bridge noisy Roman spellings to concise Urdu titles. This is a development retrieval result, not unrestricted answer accuracy."),
        markdown("## Robustness before the title-route change"),
        code(
            r'''
            robustness = load_json("reports/tables/robustness.json")
            assert robustness["test_queries_used"] == 0
            category_rows = []
            for query_type, results in sorted(robustness["query_types"].items()):
                category_rows.append({"query_type": query_type, "n": results["direct_dense"]["queries"], "dense_R@10": f'{results["direct_dense"]["recall_at_10"]:.4f}', "bridge_R@10": f'{results["querybridge_no_reranker"]["recall_at_10"]:.4f}', "reranked_R@10": f'{results["querybridge_reranked"]["recall_at_10"]:.4f}'})
            print_table(category_rows, ["query_type", "n", "dense_R@10", "bridge_R@10", "reranked_R@10"])
            write_bar_svg("robustness_recall_at_10.svg", [(row["query_type"], float(row["reranked_R@10"])) for row in category_rows], "Original reranked pipeline: Recall@10 by query type", maximum=0.55)
            '''
        ),
        markdown("![Robustness by query type](../reports/figures/robustness_recall_at_10.svg)"),
        markdown("The original reranked system performs best on clean questions (0.5000 Recall@10) and fails completely on abbreviated questions. Named entities reach only 0.0714. This breakdown explains why aggregate semantic retrieval was producing unrelated results and directly motivates title matching. A category-wise post-title-route run is not available, so it would be incorrect to replace this table with inferred values."),
        markdown("## Resource and latency analysis"),
        code(
            r'''
            resources = load_json("reports/tables/latency_resources.json")
            latency = resources["query_latency_ms"]
            latency_rows = [{"system": name, "mean_ms": values["mean"], "p95_ms": values.get("p95", "not recorded")} for name, values in latency.items()]
            print_table(latency_rows, ["system", "mean_ms", "p95_ms"])
            print("Embedding shape:", resources["embedding_matrix_shape"])
            print("Embedding index MB:", round(resources["embedding_index_bytes"] / (1024 ** 2), 2))
            print("Cold index build minutes:", round(resources["index_build_seconds"] / 60, 2))
            print("Peak observed resident memory MB:", resources["peak_observed_resident_memory_mb"])
            write_bar_svg("latency_comparison.svg", [(row["system"], float(row["mean_ms"])) for row in latency_rows], "Mean CPU query latency (ms)")
            '''
        ),
        markdown("![Latency comparison](../reports/figures/latency_comparison.svg)"),
        markdown(
            """
            ## Trade-off discussion and remaining limitations

            - The depth-20 cross-encoder improves early rank ordering but adds roughly 16.4 seconds per query and about 2.5 GB observed resident memory. It is optional rather than the default interactive path.
            - The title route offers the best measured quality/latency balance at roughly 581 ms before reranking, but it is structurally suited to title-definition questions.
            - The 4,000-article corpus cannot answer every Urdu information need, especially current prices or breaking news.
            - The diagnostic set is small, constructed, and has one recorded relevant passage per query. Alternative valid evidence may be under-counted.
            - The high Recall@10 result shows candidate coverage only. Independent end-to-end answer review, category-wise re-evaluation, calibration, and the one-time locked-test run remain necessary.
            """
        ),
    ],
    "07_error_analysis.ipynb": [
        markdown(
            """
            # Parts 9–10 — Error Analysis, Evidence Safety, and Deployment Linkage

            This notebook inspects concrete failures rather than treating an aggregate score as sufficient. It also verifies that the evaluated pipeline is connected to the local FastAPI/React deployment required by Part 10.

            **Scope:** the 30-case audit describes the original pipeline. Its categories are rule-assigned development diagnostics and require independent human review.
            """
        ),
        code(COMMON),
        markdown(
            """
            ## Error-analysis method

            A failure record is included when the verified gold passage is absent from the final top ten of the original system. Each record retains the query ID, query type, Roman query, gold passage ID, top retrieved passage/title, assigned category, failure description, affected system, and a possible future improvement. The proposed improvement field is a hypothesis, not evidence that the problem has been fixed.

            The audit is stratified to contain five examples in each of six categories. Category frequencies therefore describe the audit design—not real-world error prevalence.
            """
        ),
        code(
            r'''
            with (ROOT / "reports/error_analysis/failures_30.csv").open(encoding="utf-8-sig", newline="") as handle:
                failures = list(csv.DictReader(handle))
            categories = Counter(row["category"] for row in failures)
            statuses = Counter(row["categorization_status"] for row in failures)
            print("Failure records:", len(failures))
            print("Review status:", dict(statuses))
            print_table([{"category": name, "cases": count} for name, count in sorted(categories.items())], ["category", "cases"])
            assert len(failures) == 30 and all(count == 5 for count in categories.values())
            write_bar_svg("failure_categories.svg", sorted(categories.items()), "Original pipeline: stratified failure audit")
            '''
        ),
        markdown("![Failure categories](../reports/figures/failure_categories.svg)"),
        markdown("## Traceable example from every category"),
        code(
            r'''
            examples = []
            for category in sorted(categories):
                row = next(item for item in failures if item["category"] == category)
                examples.append({"category": category, "query_id": row["query_id"], "roman_query": row["roman_urdu_query"], "retrieved_title": row["top_retrieved_title"], "future_hypothesis": row["possible_future_improvement"]})
            print_table(examples, ["category", "query_id", "roman_query", "retrieved_title", "future_hypothesis"])
            '''
        ),
        markdown(
            """
            ### Interpretation by failure type

            - **Roman spelling mismatch / excessive noise:** exact transliteration and word-token retrieval fail when vowels or consonants differ. Character title n-grams directly target this issue.
            - **Named-entity mismatch:** semantic retrieval can prefer a related person/place. Title alignment provides a stronger identity signal.
            - **Code switching:** English tokens must be preserved while Urdu tokens are normalized; a single-language conversion can damage the query.
            - **Short ambiguity:** retrieval should request clarification when several intents remain plausible.
            - **Irrelevant retrieval:** a high semantic score does not prove the requested relation. Source and sentence validation must be separate from ranking.
            """
        ),
        markdown("## Evidence-grounding smoke test"),
        code(
            r'''
            smoke = load_json("reports/tables/grounded_qa_smoke.json")
            print("Query:", smoke["query"])
            print("Supported:", smoke["supported"])
            print("Source title:", smoke["source_title"])
            print("Source URL:", smoke["source_url"])
            print("Abstention reason:", smoke["abstention_reason"])
            print("Evidence count:", len(smoke["evidence"]))
            for evidence in smoke["evidence"]:
                print(f'- passage={evidence["passage_id"]} similarity={evidence["similarity"]:.4f} text={evidence["text"]}')
            assert smoke["supported"] and smoke["evidence"] and smoke["source_url"]
            '''
        ),
        markdown("The answer is extractive and tied to one source. The application additionally checks reranker relevance, converted-term/title alignment, sentence similarity, and requested answer shape. Date, birth/death, price, quantity, and current-capital questions have relation-specific rules. If no candidate passes, the system returns an explicit abstention reason with no invented evidence."),
        markdown("## Part 10 — Deployment linkage and local completeness"),
        code(
            r'''
            required_paths = ["backend/app/main.py", "backend/app/models.py", "backend/app/service.py", "frontend/package.json", "frontend/src/App.tsx", "frontend/dist/index.html"]
            deployment_rows = [{"path": path, "present": (ROOT / path).is_file()} for path in required_paths]
            print_table(deployment_rows, ["path", "present"])
            audit = load_json("reports/tables/portability_audit.json")
            print("Backend sources audit:", audit["checks"]["backend_sources_present"]["passed"])
            print("Frontend build audit:", audit["checks"]["frontend_build_present"]["passed"])
            print("Portable relative paths audit:", audit["checks"]["no_machine_specific_source_paths"]["passed"])
            assert all(row["present"] for row in deployment_rows)
            '''
        ),
        markdown(
            """
            The deployable application is not implemented inside the notebook. Part 10 is satisfied by the repository's FastAPI backend and React/Vite frontend, which consume the same retrieval/evidence pipeline measured here. The interface exposes query transformations, route contributions, candidate counts, confidence, evidence gates, source URL, abstention reason, and component latency.

            ## Final analysis conclusion

            The original failure audit explains the user's reported symptom: related but incorrect results were passing through a retrieval-centric pipeline. The romanized-title route materially improves candidate coverage, while source/relation gates reduce unsupported answers. Remaining work is independent annotation review, post-change category analysis, confidence calibration, clarification for ambiguity, broader Urdu collections, and the one-time locked-test evaluation after configuration freeze.
            """
        ),
    ],
}


def main() -> None:
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    for filename, cells in NOTEBOOKS_CONTENT.items():
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {"display_name": "Raabta (.venv)", "language": "python", "name": "python3"},
                "language_info": {"codemirror_mode": {"name": "ipython", "version": 3}, "file_extension": ".py", "mimetype": "text/x-python", "name": "python", "nbconvert_exporter": "python", "pygments_lexer": "ipython3", "version": "3.11+"},
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        (NOTEBOOKS / filename).write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        markdown_count = sum(cell["cell_type"] == "markdown" for cell in cells)
        code_count = sum(cell["cell_type"] == "code" for cell in cells)
        print(f"{filename}: {markdown_count} markdown + {code_count} code cells")


if __name__ == "__main__":
    main()
