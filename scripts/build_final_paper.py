"""Build the Raabta assignment report from measured development results."""

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
PDF_PATH = OUTPUTS / "raabta_assignment_report.pdf"

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
        canvas.drawString(22 * mm, 286 * mm, "RAABTA - ASSIGNMENT PROJECT REPORT")
        canvas.drawRightString(188 * mm, 14 * mm, str(doc.page))
        canvas.drawString(22 * mm, 14 * mm, "Development-set evaluation - evidence-first system")
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
\date{Assignment project report -- 20 August 2026}
\begin{document}
\maketitle
\begin{abstract}
Raabta is a CPU-first Roman-Urdu information-retrieval system that connects noisy Latin-script questions to traceable Urdu evidence. The final application combines QueryBridge variants, Urdu BM25, multilingual dense retrieval, character-level matching against romanized Urdu article titles, reciprocal rank fusion, multilingual reranking, and conservative evidence validation. On the 120-question development split, adding romanized-title retrieval increased Recall@10 from 0.1917 to 0.9833 and MRR@10 from 0.1014 to 0.5830 before reranking. The interface displays each search stage, retrieval route, validation gate, source, score, and abstention reason.
\end{abstract}
\section{Introduction}
Roman Urdu has no single standard spelling and is frequently mixed with English. Raabta addresses the resulting script mismatch as a retrieval problem: it searches a fixed Urdu Wikipedia corpus, ranks evidence, and either returns an exact sourced sentence or abstains.
\section{Data and protocol}
The local corpus contains 4,000 Urdu Wikipedia articles and 16,352 overlapping passages. The project diagnostic set contains 180 evidence-linked questions across six domains and eight noise categories. The 120-question development split is used for engineering evaluation; the separate 60-question test split is not used in the reported measurements.
\section{Method}
QueryBridge produces original, normalized Roman, Urdu-script, and retrieval-oriented query forms. A romanized-title index converts one lead title per article with uroman and uses character 2--4 grams to tolerate missing vowels and informal spellings. Title, BM25, and multilingual E5 routes are fused, then the top 20 candidates are reranked using title plus passage text. The answer layer checks relevance, query-to-source alignment, sentence similarity, requested answer type, temporal relation, and navigation boilerplate. Extraction is restricted to the validated source.
\section{Results}
The original application pipeline reached Recall@1/5/10 of 0.0750/0.1167/0.1917 and MRR@10 of 0.1014. With romanized-title retrieval, the same development check reached 0.3917/0.8750/0.9833 and MRR@10 of 0.5830. End-to-end tests additionally verify relation-aware evidence selection and safe refusal for unsupported price questions.
\section{Limitations and conclusion}
The diagnostic set is title-oriented, the corpus is limited to 4,000 articles, and development retrieval scores are not the same as answer accuracy. Live Urdu Wikipedia broadens encyclopedic coverage but is not a source for dependable current shopping prices. Within this assignment scope, Raabta demonstrates substantially stronger noisy-entity retrieval, strict evidence grounding, and a transparent user interface.
\bibliographystyle{plain}
\bibliography{references}
\end{document}
"""


def main() -> None:
    baseline = load_json("reports/tables/baselines_development.json")
    querybridge = load_json("reports/tables/querybridge_development.json")
    reranker = load_json("reports/tables/reranker_depth20.json")
    ablation = load_json("reports/tables/retrieval_ablations.json")
    robustness = load_json("reports/tables/robustness.json")
    latency = load_json("reports/tables/latency_resources.json")
    accuracy = load_json("reports/tables/application_accuracy_regression.json")

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
@misc{uroman2024,
  title={uroman: Universal Romanizer}, author={{USC Information Sciences Institute}},
  year={2024}, url={https://github.com/isi-nlp/uroman}}
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
        title="Raabta - Assignment Project Report",
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
                "Hasnat Khan  |  CPU-first NLP and Information Retrieval  |  20 August 2026",
                styles["SubTitle"],
            ),
            Spacer(1, 10 * mm),
            Paragraph(
                "ASSIGNMENT PROJECT REPORT",
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
                "This report documents the completed local application and its development-set evaluation. The 120-question development split is used for engineering measurements; the separate 60-question test split is not included in the reported scores.",
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
            "Roman Urdu is widely used in informal digital communication but has no standard spelling, is frequently code-switched with English, and differs in script from much authoritative Urdu content. Raabta is a CPU-first information-retrieval system that bridges this mismatch through controlled QueryBridge variants, Urdu BM25, multilingual dense retrieval, character-level matching against romanized Urdu titles, reciprocal rank fusion, multilingual reranking, and evidence validation. On the 120-question development split, adding the romanized-title route increased Recall@10 from 0.1917 to 0.9833 and MRR@10 from 0.1014 to 0.5830 before reranking. The application returns an exact sentence from a validated source or abstains, while the interface exposes every route, score, gate, source, decision, and latency component.",
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
            "2. Data and evaluation protocol",
            "The primary corpus is a deterministic 4,000-article subset of the 20231101 Urdu Wikipedia snapshot [2]. Cleaning preserves article identity, title, URL, raw text, normalized text, and an auditable six-domain assignment. The default passage collection contains 16,352 passages of up to 150 whitespace tokens with 30-token overlap. The passage file SHA-256 is 47648cf679facb9a576841542289767f854c1a27aca6cb8e14e3f3eb1a2e5671. A supporting Roman-Urdu parallel slice supplies transliteration evidence only; it is not used as relevance supervision.",
        ),
        (
            "2.1 Diagnostic set",
            "The Raabta Diagnostic Set contains 180 evidence-linked title-definition questions balanced across culture, general, geography, history, Pakistan, and science. It includes clean, informal, highly noisy, abbreviated, code-switched, named-entity, short, and slightly ambiguous queries. Each record stores its target passage and evidence text. The split contains 120 development questions and a separate 60-question test partition. The reported assignment measurements use only the development partition.",
        ),
        (
            "3. System method",
            "QueryBridge creates no more than four traceable candidates: (1) the original query, (2) conservatively normalized Roman Urdu, (3) Urdu-script transliteration derived from a supporting lexicon, and (4) a controlled retrieval-oriented representation. Each candidate records its method, source query, semantic similarity, conversion coverage, and accept/reject reason. Accepted variants traverse title-boosted Unicode BM25 and exact normalized multilingual E5 retrieval [3]. A separate title route romanizes one lead Urdu title per article and applies character 2-4 gram matching, which is robust to missing vowels, abbreviations, and informal entity spelling. Weighted RRF combines these routes without treating their scores as calibrated probabilities.",
        ),
        (
            "3.1 Reranking and grounded answers",
            "The interactive application reranks the top 20 fused candidates with Alibaba-NLP/gte-multilingual-reranker-base using pinned weights and custom-code revisions. Each pair contains the article title and passage text. Before an answer is displayed, the top source must pass a 0.62 reranker threshold and either converted-term overlap or cross-script title alignment. The selected sentence must exceed 0.70 semantic similarity and satisfy the requested relation: for example, a birth question requires birth wording, a price requires a currency amount, and a current-capital question rejects historical statements. Navigation text and generic list descriptions are rejected. Extraction is restricted to the exact source that passed validation.",
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
    app_after = accuracy["after"]
    rows.append(
        [
            "Final retrieval + title route",
            f"{app_after['recall_at_1']:.4f}",
            f"{app_after['recall_at_5']:.4f}",
            f"{app_after['recall_at_10']:.4f}",
            f"{app_after['mrr_at_10']:.4f}",
            f"{app_after['ndcg_at_10']:.4f}",
            "580.8",
        ]
    )
    story.extend(
        [
            Paragraph("5. Development results", styles["Section"]),
            Paragraph(
                "Table 1 retains the original baseline measurements and adds the final application retrieval regression. The romanized-title route produces the largest improvement because it directly addresses noisy named entities and missing-vowel spellings. Recall@10 rises from 0.1917 in the previous application pipeline to 0.9833, while MRR@10 rises from 0.1014 to 0.5830 before interactive reranking.",
                styles["BodyJ"],
            ),
            metric_table(rows, [44 * mm, 15 * mm, 15 * mm, 17 * mm, 19 * mm, 20 * mm, 20 * mm]),
            Paragraph(
                "Table 1. Development-only retrieval results (n=120; test queries used=0).",
                styles["Caption"],
            ),
            bar_chart(
                ["Dense", "Trans+BM25", "Hybrid", "QueryBridge", "+Rerank", "+Title route"],
                [
                    systems["direct_dense"]["recall_at_10"],
                    systems["single_transliteration_bm25"]["recall_at_10"],
                    systems["standard_hybrid"]["recall_at_10"],
                    qb["recall_at_10"],
                    rr["recall_at_10"],
                    app_after["recall_at_10"],
                ],
                "Recall@10 by system - development only",
            ),
            Paragraph(
                "Figure 1. Character-level romanized-title matching raises development Recall@10 to 0.9833.",
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
                "The original pipeline varied sharply by query type: clean queries reached Recall@10 of 0.5000 while abbreviated queries reached 0.0000. That failure analysis motivated the character-level title route. The final aggregate regression reaches 0.9833 Recall@10 on the same development questions, although the small title-oriented categories should still be interpreted as assignment diagnostics rather than broad language-performance estimates.",
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
                "The original ablations show that transliteration, dense retrieval, and RRF carry the largest positive contributions. BM25 and normalization add smaller gains, while controlled expansion is mixed. The subsequent title-route regression is reported separately because it changes the candidate-generation architecture rather than removing one component from the original system.",
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
                "A traceable 30-case audit identified Roman spelling mismatch, excessive noise, code switching, named-entity mismatch, short or ambiguous queries, and irrelevant retrieval. The final system implements the principal remedies: character-level title matching, improved query conversion, title-aware reranking, strict source alignment, relation-aware answer validation, current-versus-historical checks, navigation-text rejection, and safe abstention.",
                styles["BodyJ"],
            ),
            Paragraph("5.4 Latency and resource trade-offs", styles["SubSection"]),
            Paragraph(
                f"The 16,352 x 384 float32 embedding matrix occupies {latency['embedding_index_bytes'] / 1_000_000:.1f} MB and required {latency['index_build_seconds'] / 60:.1f} minutes for cold CPU embedding generation and serialization. Direct dense retrieval averages {latency['query_latency_ms']['direct_dense']['mean']:.1f} ms, while the original QueryBridge retrieval averages {latency['query_latency_ms']['querybridge_no_reranker']['mean']:.1f} ms. The final romanized-title retrieval regression averages about 580.8 ms before reranking. Depth-20 reranking remains the main CPU cost at roughly {latency['query_latency_ms']['reranker_depth20']['mean'] / 1000:.1f} seconds, but it is retained in the application because answer precision is prioritized over speed.",
                styles["BodyJ"],
            ),
        ]
    )

    final_sections = [
        (
            "6. Application architecture",
            "The complete local application uses a FastAPI backend and responsive React/Vite frontend. A query first passes through normalization and transliteration, character-level title matching, BM25 and dense retrieval, weighted fusion, cross-encoder reranking, and grounded evidence validation. The response records each completed stage, every active route and candidate count, accepted and rejected query variants, observed gate values and thresholds, source titles and URLs, candidate snippets, final decision reasons, and component latency. The live Urdu Wikipedia fallback is explicitly user-controlled and remains off by default.",
        ),
        (
            "6.1 Evidence and abstention",
            "Every supported answer is a direct substring of the exact source that passed validation. The query 'pakistan ka capital kya hai' returns the current Islamabad statement while rejecting historical Karachi and navigation-list sentences. A noisy Sweden-feminism query resolves to the correct article through romanized-title matching, and a Jinnah birth query requires an explicit birth relation. Unsupported current-price questions return a fixed Urdu abstention with no citation instead of a plausible-looking number.",
        ),
        (
            "7. Reproducibility",
            "All Python runtime, development, build, and frontend dependencies are pinned, including uroman 1.3.1.1 for Urdu-title romanization. Dataset and model identifiers and revisions are stored in configuration and manifests. Passage and embedding checksums are verified by the portability audit. The setup script recreates the isolated Python environment and frontend dependencies on another PC; the transfer archive excludes .venv, node_modules, caches, temporary work, and repository metadata.",
        ),
        (
            "8. Limitations, ethics, and threats to validity",
            "The 4,000-article corpus cannot cover every topic, and the development questions are title-oriented, so the 0.9833 Recall@10 measurement is not an answer-accuracy percentage or a guarantee for arbitrary queries. The live fallback improves encyclopedic coverage but is not suitable for dependable current shopping prices or breaking news. Group sizes are small, the separate test partition is not used here, and Wikipedia licensing and attribution must be preserved. The system is an evidence-retrieval assignment prototype rather than an authoritative decision engine.",
        ),
        (
            "9. Conclusion",
            "Raabta demonstrates a complete CPU-first path from noisy Roman-Urdu input to traceable Urdu evidence. The strongest improvement comes from matching noisy Roman entities directly against romanized Urdu titles, which raises development Recall@10 from 0.1917 to 0.9833. Title-aware reranking, strict source selection, relation-aware sentence checks, and safe abstention prevent the retrieval gain from turning into unsupported answers. The frontend makes the complete decision path visible instead of presenting an unexplained result.",
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
            Paragraph(
                "[5] USC Information Sciences Institute. uroman: Universal Romanizer, version 1.3.1.1. https://github.com/isi-nlp/uroman",
                styles["Ref"],
            ),
            Spacer(1, 4 * mm),
            Paragraph("Appendix A. Frozen identifiers", styles["Section"]),
            Paragraph(
                "Dense model: intfloat/multilingual-e5-small @ d1d99a1efae6779390caba937d92c54b5bc70e51. Reranker weights: Alibaba-NLP/gte-multilingual-reranker-base @ a6258e9d2b1a11aa7bccdff9efde562bbca4393d. Reranker custom code: 40ced75c3017eb27626c9d4ea981bde21a2662f4. Urdu Wikipedia revision: 3e1f92c331f318af862b87e2319ed5dc26d80f5d. Diagnostic SHA-256: 98f723f1e5cb8f1ece24a11192052e7a2119629703e001084c0bdcadbfe37cfd.",
                styles["BodyJ"],
            ),
            Paragraph("Appendix B. Assignment scope", styles["Section"]),
            Paragraph(
                "This submission includes the local application, pinned dependencies, corpus and model artifacts, evaluation reports, documentation, report source, compiled report, setup instructions, tests, and a portable transfer archive. Slides are intentionally excluded from the final transfer package.",
                styles["BodyJ"],
            ),
        ]
    )

    doc.build(story)
    shutil.copy2(PDF_PATH, PAPER / "main.pdf")
    print(PDF_PATH)


if __name__ == "__main__":
    main()
