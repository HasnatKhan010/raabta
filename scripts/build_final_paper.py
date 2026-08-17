"""Build the Raabta development research paper from measured results."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
OUTPUTS = ROOT / "outputs"
PDF_PATH = OUTPUTS / "raabta_research_paper.pdf"

INK = colors.HexColor("#173F40")
ACCENT = colors.HexColor("#B7482B")
TEAL = colors.HexColor("#297570")
CREAM = colors.HexColor("#F3EEE3")
MUTED = colors.HexColor("#607171")
RULE = colors.HexColor("#D7D2C7")


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def page_chrome(canvas, doc) -> None:
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(RULE)
        canvas.line(22 * mm, 282 * mm, 188 * mm, 282 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(22 * mm, 286 * mm, "RAABTA - DEVELOPMENT STUDY")
        canvas.drawRightString(188 * mm, 14 * mm, str(doc.page))
        canvas.drawString(
            22 * mm, 14 * mm, "Locked test set unused - independent language review pending"
        )
    canvas.restoreState()


def metric_table(data: list[list[str]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), INK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("LEADING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def bar_chart(labels: list[str], values: list[float], title: str) -> Drawing:
    drawing = Drawing(470, 220)
    chart = VerticalBarChart()
    chart.x = 48
    chart.y = 45
    chart.height = 135
    chart.width = 390
    chart.data = [values]
    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.angle = 20
    chart.categoryAxis.labels.dy = -9
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(values) * 1.25 if values else 1
    chart.valueAxis.labels.fontSize = 7
    chart.valueAxis.gridStrokeColor = RULE
    chart.bars[0].fillColor = TEAL
    chart.bars[0].strokeColor = TEAL
    drawing.add(chart)
    drawing.add(
        String(
            235,
            204,
            title,
            textAnchor="middle",
            fontName="Helvetica-Bold",
            fontSize=11,
            fillColor=INK,
        )
    )
    return drawing


def latex_source() -> str:
    return r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=25mm]{geometry}
\usepackage{booktabs,graphicx,hyperref,xcolor}
\title{Raabta: Script-Aware Multi-Query Reformulation and Evidence Retrieval for Roman-Urdu Questions}
\author{Hasnat Khan}
\date{Development study -- 16 August 2026}
\begin{document}
\maketitle
\begin{abstract}
Roman Urdu is common in digital communication but lacks standard spelling and often mixes with English, while much authoritative content remains in Urdu script. Raabta studies a CPU-first retrieval pipeline that preserves the original query, applies conservative normalization, generates controlled Roman and Urdu-script variants, retrieves through BM25 and multilingual dense routes, combines rankings using reciprocal rank fusion, and optionally reranks a small candidate set. On 120 automatically curated and programmatically checked development questions, QueryBridge raised Recall@10 from 0.0917 for direct dense retrieval to 0.1667; depth-20 reranking raised MRR@10 from 0.0750 to 0.1444. The 60-question test set remains locked and independent native-speaker review is pending.
\end{abstract}
\section{Introduction}
Raabta asks whether controlled script-aware query representations improve retrieval over a fixed Urdu Wikipedia corpus. The contribution is narrower than prior Roman-Urdu benchmark work: it studies multi-query reformulation, complementary retrieval routes, transparent fusion, lightweight reranking, and evidence-first answering.
\section{Data and protocol}
The frozen corpus contains 4,000 Urdu Wikipedia articles and 16,352 overlapping passages of 150 tokens with 30-token overlap. A 180-question diagnostic set covers six domains and eight query types, split into 120 development and 60 locked test questions before tuning.
\section{Method}
QueryBridge produces at most four traceable representations: original, normalized Roman Urdu, Urdu-script transliteration, and a retrieval-oriented variant. Variants below a semantic-similarity threshold are rejected. Accepted variants independently traverse BM25 and multilingual E5 retrieval routes and are fused with reciprocal rank fusion. A pinned multilingual cross-encoder reranks the top 20 offline. Answers are exact evidence sentences with a source URL or an explicit abstention.
\section{Results}
Development-only measurements show QueryBridge Recall@10 of 0.1667 and MRR@10 of 0.0750. Reranking improves Recall@10 to 0.1833 and MRR@10 to 0.1444, at a mean reranking latency of 16.4 seconds on CPU. Ablations identify transliteration, dense retrieval, and rank fusion as the strongest positive contributors. Controlled expansion is not uniformly helpful.
\section{Limitations and conclusion}
The annotations and first-pass failure categories require independent native-speaker review. The diagnostic set uses deterministic title-definition construction and is not globally representative. The test set has not been evaluated. Within those limits, the development evidence supports continuing script-aware multi-query retrieval while redesigning expansion and using a shallower reranker for interactive deployment.
\bibliographystyle{plain}
\bibliography{references}
\end{document}
"""


def main() -> None:
    baseline = load_json("reports/tables/provisional_baselines_development.json")
    querybridge = load_json("reports/tables/provisional_querybridge_development.json")
    reranker = load_json("reports/tables/provisional_reranker_depth20.json")
    ablation = load_json("reports/tables/provisional_retrieval_ablations.json")
    robustness = load_json("reports/tables/provisional_robustness.json")
    latency = load_json("reports/tables/provisional_latency_resources.json")

    PAPER.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    (PAPER / "main.tex").write_text(latex_source(), encoding="utf-8")
    (PAPER / "references.bib").write_text(
        """@inproceedings{butt2025ir,
  title={Roman Urdu as a Low-Resource Language: Building the First IR Dataset and Baseline},
  author={Butt, Muhammad Umer Tariq and Varanasi, Stalin and Neumann, Guenter},
  booktitle={Proceedings of the First Workshop on Advancing NLP for Low-Resource Languages},
  pages={82--87}, year={2025}, url={https://aclanthology.org/2025.lowresnlp-1.9/}}
@article{wang2024e5,
  title={Multilingual E5 Text Embeddings: A Technical Report},
  author={Wang, Liang and others}, journal={arXiv preprint arXiv:2402.05672}, year={2024}}
@misc{wikimedia2023urdu,
  title={Wikimedia Wikipedia dataset: 20231101.ur}, year={2023},
  url={https://huggingface.co/datasets/wikimedia/wikipedia/tree/3e1f92c331f318af862b87e2319ed5dc26d80f5d/20231101.ur}}
""",
        encoding="utf-8",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="PaperTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=25,
            leading=30,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=16,
            textColor=MUTED,
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=INK,
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=TEAL,
            spaceBefore=10,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyJ",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13.2,
            alignment=TA_JUSTIFY,
            textColor=colors.HexColor("#263638"),
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=ACCENT,
            borderColor=ACCENT,
            borderWidth=1,
            borderPadding=8,
            backColor=colors.HexColor("#FAF1EC"),
            spaceBefore=8,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            fontSize=7.5,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Ref",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
            leftIndent=10,
            firstLineIndent=-10,
            textColor=colors.HexColor("#344849"),
            spaceAfter=5,
        )
    )

    doc = BaseDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title="Raabta - Research Paper",
        author="Hasnat Khan",
    )
    doc.addPageTemplates(
        PageTemplate(
            id="main",
            frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")],
            onPage=page_chrome,
        )
    )
    story = []
    story.extend(
        [
            Spacer(1, 22 * mm),
            Paragraph(
                "RAABTA",
                ParagraphStyle(
                    name="Mark",
                    fontName="Helvetica-Bold",
                    fontSize=10,
                    tracking=4,
                    textColor=ACCENT,
                    spaceAfter=12,
                ),
            ),
            Paragraph(
                "Script-Aware Multi-Query Reformulation and Evidence Retrieval for Roman-Urdu Questions",
                styles["PaperTitle"],
            ),
            Paragraph(
                "Hasnat Khan  |  CPU-first NLP and Information Retrieval  |  16 August 2026",
                styles["SubTitle"],
            ),
            Spacer(1, 10 * mm),
            Paragraph(
                "DEVELOPMENT STUDY",
                ParagraphStyle(
                    name="Status",
                    fontName="Helvetica-Bold",
                    fontSize=11,
                    textColor=colors.white,
                    backColor=ACCENT,
                    borderPadding=8,
                    alignment=TA_CENTER,
                ),
            ),
            Spacer(1, 8 * mm),
            Paragraph(
                "The reported measurements use 120 automatically curated and programmatically checked development questions. The 60-question test split remains locked, and independent native-speaker review is pending. This document reports development measurements and does not make a test-set benchmark claim.",
                styles["Callout"],
            ),
            Spacer(1, 16 * mm),
            Paragraph("Research question", styles["SubSection"]),
            Paragraph(
                "Can script-aware multi-query reformulation improve retrieval effectiveness for noisy Roman-Urdu questions over Urdu-script knowledge bases compared with direct retrieval, single transliteration, and standard hybrid retrieval?",
                styles["BodyJ"],
            ),
            PageBreak(),
        ]
    )

    sections = [
        (
            "Abstract",
            "Roman Urdu is widely used in informal digital communication but has no standard spelling, is frequently code-switched with English, and differs in script from much authoritative Urdu content. Raabta studies whether a small, controlled set of meaning-preserving query representations can bridge Roman-Urdu questions to Urdu-script evidence. The system preserves the original query, applies conservative normalization, produces supporting-data transliteration and a retrieval-oriented variant, rejects semantic drift, retrieves through BM25 and multilingual E5 routes, fuses rankings with reciprocal rank fusion (RRF), and optionally reranks a bounded candidate set. On 120 development questions, QueryBridge improves Recall@10 from 0.0917 for direct dense retrieval to 0.1667. A depth-20 multilingual reranker improves MRR@10 from 0.0750 to 0.1444, but averages 16.4 seconds on CPU. The application returns exact evidence sentences, sources, traces, latency, and explicit abstention. Results remain provisional because independent language review is pending and the frozen 60-question test split has not been used.",
        ),
        (
            "1. Introduction",
            "Roman Urdu creates an information-access mismatch: users often type Urdu using Latin characters, while a large body of relevant knowledge is written in Urdu script. Variation such as kia/kya, hai/hy, abbreviations, phonetic spelling, named entities, and English insertions weakens exact lexical matching. Direct multilingual dense retrieval can cross scripts, but it may not reliably handle extreme noise or surface-form mismatch. Raabta treats this as a retrieval and evidence problem rather than as a generic chatbot problem.",
        ),
        (
            "1.1 Positioning and contribution",
            "Butt, Varanasi, and Neumann (2025) introduced a large-scale Roman-Urdu information-retrieval dataset and multilingual baseline [1]. Raabta does not claim that Roman-Urdu IR is unstudied. Its narrower contribution is to evaluate transparent, controlled multi-query representations over a fixed Urdu-script corpus, combine complementary retrieval routes, measure which components contribute, and expose an evidence-first local application. The research contribution is therefore the script-aware query bridge and its controlled evaluation, not the use of a large language model.",
        ),
        (
            "2. Data and frozen protocol",
            "The primary corpus is a deterministic 4,000-article subset of the 20231101 Urdu Wikipedia snapshot [2]. Cleaning preserves article identity, title, URL, raw text, normalized text, and an auditable six-domain assignment. The default passage collection contains 16,352 passages of up to 150 whitespace tokens with 30-token overlap. The passage file SHA-256 is 47648cf679facb9a576841542289767f854c1a27aca6cb8e14e3f3eb1a2e5671. A supporting Roman-Urdu parallel slice supplies transliteration evidence only; it is not used as relevance supervision.",
        ),
        (
            "2.1 Diagnostic set",
            "The Raabta Diagnostic Set contains 180 automatically curated title-definition questions balanced across culture, general, geography, history, Pakistan, and science. It includes clean, informal, highly noisy, abbreviated, code-switched, named-entity, short, and slightly ambiguous queries. Passage IDs and exact evidence strings were programmatically checked against the frozen corpus. The split was frozen before tuning: 120 development questions and 60 test questions. Independent native-speaker review is required before making final benchmark claims.",
        ),
        (
            "3. System method",
            "QueryBridge creates no more than four traceable candidates: (1) the original query, (2) conservatively normalized Roman Urdu, (3) Urdu-script transliteration derived from a supporting lexicon, and (4) a controlled retrieval-oriented representation. Each candidate records its method, source query, semantic similarity, and accept/reject reason. A pinned multilingual E5-small encoder [3] filters semantic drift at a 0.55 cosine threshold. Accepted variants independently traverse Unicode BM25 and exact normalized dense retrieval. Equal-weight RRF combines incomparable route scores without pretending they are calibrated probabilities.",
        ),
        (
            "3.1 Reranking and grounded answers",
            "The top 20 fused candidates can be reranked with Alibaba-NLP/gte-multilingual-reranker-base using pinned model and custom-code revisions. Because the depth-20 cross-encoder is slow on CPU, it is used for offline evaluation; the interactive API currently uses fused retrieval without reranking. The answer layer splits the top passages into sentences, compares accepted QueryBridge representations with source sentences, and returns the strongest coherent one- or two-sentence extract. If no evidence exists or similarity falls below 0.70, it returns an Urdu abstention with no citation.",
        ),
        (
            "4. Experimental design",
            "The frozen baselines are direct dense retrieval, one-best deterministic transliteration plus BM25, and a standard raw-query BM25+dense RRF hybrid. Metrics are Recall@1, Recall@5, Recall@10, MRR@10, and nDCG@10. All development metrics are macro averages over 120 questions. Latency excludes cold model loading unless explicitly stated. Robustness is reported by eight query categories. Retrieval-component ablations remove normalization, transliteration, expansion, BM25, dense retrieval, or RRF; the paired before/after reranker measurement isolates reranking.",
        ),
    ]
    for title, body in sections:
        story.append(
            Paragraph(
                title, styles["Section"] if "." not in title.split()[0] else styles["Section"]
            )
        )
        story.append(Paragraph(body, styles["BodyJ"]))

    systems = baseline["systems"]
    rows = [["System", "R@1", "R@5", "R@10", "MRR@10", "nDCG@10", "Mean ms"]]
    labels = {
        "direct_dense": "Direct dense",
        "single_transliteration_bm25": "Single transliteration + BM25",
        "standard_hybrid": "Standard hybrid",
    }
    for key in ("direct_dense", "single_transliteration_bm25", "standard_hybrid"):
        item = systems[key]
        rows.append(
            [
                labels[key],
                f"{item['recall_at_1']:.4f}",
                f"{item['recall_at_5']:.4f}",
                f"{item['recall_at_10']:.4f}",
                f"{item['mrr_at_10']:.4f}",
                f"{item['ndcg_at_10']:.4f}",
                f"{item['mean_latency_ms']:.1f}",
            ]
        )
    qb = querybridge["result"]
    rows.append(
        [
            "QueryBridge + RRF",
            f"{qb['recall_at_1']:.4f}",
            f"{qb['recall_at_5']:.4f}",
            f"{qb['recall_at_10']:.4f}",
            f"{qb['mrr_at_10']:.4f}",
            f"{qb['ndcg_at_10']:.4f}",
            f"{qb['mean_latency_ms']:.1f}",
        ]
    )
    rr = reranker["after_reranking"]
    rows.append(
        [
            "QueryBridge + reranker",
            f"{rr['recall_at_1']:.4f}",
            f"{rr['recall_at_5']:.4f}",
            f"{rr['recall_at_10']:.4f}",
            f"{rr['mrr_at_10']:.4f}",
            f"{rr['ndcg_at_10']:.4f}",
            f"{reranker['mean_retrieval_ms'] + reranker['mean_rerank_ms']:.1f}",
        ]
    )
    story.extend(
        [
            Paragraph("5. Development results", styles["Section"]),
            Paragraph(
                "Table 1 compares all frozen systems. QueryBridge produces the best Recall@10 before reranking, while the cross-encoder primarily improves early ordering. The result supports the development hypothesis but does not establish final generalization.",
                styles["BodyJ"],
            ),
            metric_table(rows, [44 * mm, 15 * mm, 15 * mm, 17 * mm, 19 * mm, 20 * mm, 20 * mm]),
            Paragraph(
                "Table 1. Development-only retrieval results (n=120; test queries used=0).",
                styles["Caption"],
            ),
            bar_chart(
                ["Dense", "Trans+BM25", "Hybrid", "QueryBridge", "+Rerank"],
                [
                    systems["direct_dense"]["recall_at_10"],
                    systems["single_transliteration_bm25"]["recall_at_10"],
                    systems["standard_hybrid"]["recall_at_10"],
                    qb["recall_at_10"],
                    rr["recall_at_10"],
                ],
                "Recall@10 by system - development only",
            ),
            Paragraph(
                "Figure 1. QueryBridge raises candidate recall; reranking gives a smaller additional Recall@10 gain.",
                styles["Caption"],
            ),
        ]
    )

    robust_rows = [["Query type", "n", "Reranked R@10", "Reranked MRR@10"]]
    for name, values in robustness["query_types"].items():
        item = values["querybridge_reranked"]
        robust_rows.append(
            [
                name.replace("_", " "),
                str(item["queries"]),
                f"{item['recall_at_10']:.4f}",
                f"{item['mrr_at_10']:.4f}",
            ]
        )
    story.extend(
        [
            Paragraph("5.1 Robustness", styles["SubSection"]),
            Paragraph(
                "Performance varies sharply by query type. Clean queries reach Recall@10 of 0.5000, while abbreviated queries reach 0.0000. Highly noisy, short, and code-switched queries retain some signal, but informal spelling and named entities remain difficult. These small group counts are diagnostic, not population estimates.",
                styles["BodyJ"],
            ),
            metric_table(robust_rows, [65 * mm, 15 * mm, 36 * mm, 40 * mm]),
            Paragraph("Table 2. Reranked robustness by frozen query category.", styles["Caption"]),
        ]
    )

    abl_rows = [["Configuration", "R@10", "MRR@10", "Mean ms", "Delta R@10"]]
    full = ablation["configurations"]["full_no_reranker"]
    for name, item in ablation["configurations"].items():
        abl_rows.append(
            [
                name.replace("_", " "),
                f"{item['recall_at_10']:.4f}",
                f"{item['mrr_at_10']:.4f}",
                f"{item['mean_latency_ms']:.1f}",
                f"{item['recall_at_10'] - full['recall_at_10']:+.4f}",
            ]
        )
    story.extend(
        [
            Paragraph("5.2 Ablation study", styles["SubSection"]),
            Paragraph(
                "Removing transliteration, dense retrieval, or RRF causes the largest Recall@10 losses. BM25 and normalization add smaller positive gains. The expansion rule is not uniformly beneficial: removing it lowers Recall@10 slightly but improves MRR@10. This negative result argues for redesign rather than post-hoc defense. Retrieval controls are measured before reranking to isolate retrieval behavior; a final reranker-retained matrix remains pending for the main PC.",
                styles["BodyJ"],
            ),
            metric_table(abl_rows, [55 * mm, 23 * mm, 25 * mm, 25 * mm, 28 * mm]),
            Paragraph(
                "Table 3. Retrieval-stage leave-one-component-out controls (n=120).",
                styles["Caption"],
            ),
        ]
    )

    story.extend(
        [
            Paragraph("5.3 Error analysis", styles["SubSection"]),
            Paragraph(
                "A traceable 30-case audit balances six observed categories: Roman spelling mismatch, excessive spelling noise, code-switching failure, named-entity mismatch, short/ambiguous query, and irrelevant retrieval. Each row records the real query, gold passage, top retrieved passage and title, affected system, likely cause, and a possible improvement. Labels are deterministic first-pass assignments and explicitly require human review. The dominant engineering remedies are character-level normalization, language-aware token handling, entity aliases, clarification for underspecified queries, and reviewed hard negatives.",
                styles["BodyJ"],
            ),
            Paragraph("5.4 Latency and resource trade-offs", styles["SubSection"]),
            Paragraph(
                f"The 16,352 x 384 float32 embedding matrix occupies {latency['embedding_index_bytes'] / 1_000_000:.1f} MB and required {latency['index_build_seconds'] / 60:.1f} minutes for cold CPU embedding generation and serialization. Direct dense retrieval averages {latency['query_latency_ms']['direct_dense']['mean']:.1f} ms; QueryBridge averages {latency['query_latency_ms']['querybridge_no_reranker']['mean']:.1f} ms. Depth-20 reranking averages {latency['query_latency_ms']['reranker_depth20']['mean'] / 1000:.1f} seconds and observed process resident memory reached {latency['peak_observed_resident_memory_mb'] / 1024:.2f} GB. The quality gain is meaningful offline but impractical for the interactive CPU path at depth 20.",
                styles["BodyJ"],
            ),
        ]
    )

    final_sections = [
        (
            "6. Application architecture",
            "The complete local application uses a FastAPI backend and responsive React/Vite frontend. The backend exposes health, query, comparison, source, and configuration endpoints with Pydantic validation and an explicit local CORS allowlist. A query response contains the original query, accepted and rejected variants, exact answer, evidence spans, sources, retrieval trace, non-probabilistic scores, and component latency. Research Mode compares Direct Dense, Single Transliteration, Standard Hybrid, and Raabta. It reports NOT PROVIDED when a free-form query has no gold label and NOT RETRIEVED when supplied verified evidence is absent.",
        ),
        (
            "6.1 Evidence and abstention",
            "Every supported answer is a direct substring of a retrieved source passage. The real-corpus smoke query 'pakistan ka capital kya hai' retrieves the Urdu Wikipedia article about Pakistan's capitals at rank 1 and returns the exact sentence stating that Islamabad has been the national or federal capital since 1960. When candidates are absent or evidence similarity is below threshold, the system returns a fixed Urdu abstention, no evidence, and no source. This prevents unsupported generation by construction.",
        ),
        (
            "7. Reproducibility",
            "All Python runtime, development, build, and frontend dependencies are pinned. Dataset and model identifiers and revisions are stored in configuration and manifests. The passage and embedding checksums are verified by a portability audit. Seven notebooks execute from top to bottom with fixed seed 20250816 and visible outputs. The main Phase 6 command regenerates tables, figures, latency reporting, and the error audit from measured artifacts. A fresh Python 3.12 environment successfully builds and imports the local package. The project excludes .venv and node_modules so they can be recreated on another PC.",
        ),
        (
            "8. Limitations, ethics, and threats to validity",
            "The most important limitation is annotation independence: the initial questions and evidence checks were automated, so a native Roman-Urdu/Urdu reviewer must confirm naturalness, intent, evidence, and failure categories. Title-definition construction may favor encyclopedic queries and the 4,000-article sample is not representative of all Urdu information needs. The semantic drift threshold and deterministic expansion were tuned only for engineering feasibility. Group sizes are small. The test set remains locked. Wikipedia licensing and attribution must be preserved, and the diagnostic CSV should not be published without a redistribution review. The system should be presented as an information-retrieval prototype, not an authoritative answer engine.",
        ),
        (
            "9. Conclusion",
            "Raabta demonstrates a complete CPU-first path from noisy Roman-Urdu input to traceable Urdu evidence. On the provisional development split, controlled multi-query retrieval improves Recall@10 over direct dense and standard hybrid baselines, while reranking improves early ranking at substantial latency cost. Transliteration, dense retrieval, and RRF are the strongest observed components; the current expansion rule is mixed. The strongest practical contribution is a transparent system that exposes what was changed, which routes contributed, which evidence supports the answer, and when the system abstains. Final scientific claims await independent review and one-time locked test evaluation.",
        ),
    ]
    for title, body in final_sections:
        story.append(
            Paragraph(title, styles["Section"] if title[0].isdigit() else styles["SubSection"])
        )
        story.append(Paragraph(body, styles["BodyJ"]))

    story.extend(
        [
            Paragraph("References", styles["Section"]),
            Paragraph(
                "[1] Muhammad Umer Tariq Butt, Stalin Varanasi, and Guenter Neumann. Roman Urdu as a Low-Resource Language: Building the First IR Dataset and Baseline. LowResNLP 2025, pp. 82-87. https://aclanthology.org/2025.lowresnlp-1.9/",
                styles["Ref"],
            ),
            Paragraph(
                "[2] Wikimedia. Wikipedia dataset, Urdu configuration 20231101.ur, frozen revision 3e1f92c331f318af862b87e2319ed5dc26d80f5d. CC BY-SA 3.0 and GFDL. https://huggingface.co/datasets/wikimedia/wikipedia",
                styles["Ref"],
            ),
            Paragraph(
                "[3] Liang Wang et al. Multilingual E5 Text Embeddings: A Technical Report. arXiv:2402.05672, 2024. Model card: https://huggingface.co/intfloat/multilingual-e5-small",
                styles["Ref"],
            ),
            Paragraph(
                "[4] Muhammad Umer Tariq Butt, Stalin Varanasi, and Guenter Neumann. Low-Resource Transliteration for Roman-Urdu and Urdu. LoResMT 2025, pp. 144-153. https://aclanthology.org/2025.loresmt-1.13/",
                styles["Ref"],
            ),
            Spacer(1, 4 * mm),
            Paragraph("Appendix A. Frozen identifiers", styles["Section"]),
            Paragraph(
                "Dense model: intfloat/multilingual-e5-small @ d1d99a1efae6779390caba937d92c54b5bc70e51. Reranker weights: Alibaba-NLP/gte-multilingual-reranker-base @ a6258e9d2b1a11aa7bccdff9efde562bbca4393d. Reranker custom code: 40ced75c3017eb27626c9d4ea981bde21a2662f4. Urdu Wikipedia revision: 3e1f92c331f318af862b87e2319ed5dc26d80f5d. Diagnostic SHA-256: 98f723f1e5cb8f1ece24a11192052e7a2119629703e001084c0bdcadbfe37cfd.",
                styles["BodyJ"],
            ),
            Paragraph("Appendix B. Definition of finalization", styles["Section"]),
            Paragraph(
                "Finalization requires: (1) independent native-speaker review of all diagnostic questions and failure labels; (2) corrections made without examining test retrieval outputs; (3) final configuration frozen; (4) one-time evaluation on the 60 locked test questions; (5) replacement of provisional tables and figures; and (6) retention of development and test results as separate, clearly labeled analyses.",
                styles["BodyJ"],
            ),
        ]
    )

    doc.build(story)
    shutil.copy2(PDF_PATH, PAPER / "main.pdf")
    print(PDF_PATH)


if __name__ == "__main__":
    main()
