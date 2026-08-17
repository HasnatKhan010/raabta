# Phase 6 — provisional evaluation and analysis

Run date: 2026-08-16. This analysis uses all 120 Codex-verified development records and zero locked test records. It is engineering evidence, not a final-paper result, until independent native-speaker review is complete.

## Robustness

| Query type | Questions | Reranked Recall@10 | Reranked MRR@10 |
|---|---:|---:|---:|
| Clean Roman Urdu | 16 | 0.5000 | 0.3385 |
| Highly noisy Roman Urdu | 15 | 0.2667 | 0.2222 |
| Short query | 15 | 0.2667 | 0.2167 |
| Urdu-English code-switching | 14 | 0.2143 | 0.2143 |
| Named entity | 14 | 0.0714 | 0.0238 |
| Slightly ambiguous | 15 | 0.0667 | 0.0667 |
| Informal spelling | 16 | 0.0625 | 0.0625 |
| Abbreviated Roman Urdu | 15 | 0.0000 | 0.0000 |

The aggregate result hides important behavior. Clean queries are substantially easier, while abbreviation and informal spelling remain major weaknesses. This small diagnostic set does not justify broad population claims.

## Component ablations

The six retrieval controls are measured before reranking so they isolate retrieval behavior without spending several additional CPU-hours on repeated cross-encoder runs. The separately paired full/no-reranker result isolates reranking. A final-paper leave-one-out matrix with reranking retained for every retrieval control remains pending for the main PC.

| Retrieval configuration | Recall@10 | MRR@10 | Mean latency |
|---|---:|---:|---:|
| Full retrieval, no reranker | 0.1667 | 0.0750 | 425.2 ms |
| No normalization | 0.1500 | 0.0715 | 402.9 ms |
| No transliteration | 0.0667 | 0.0253 | 335.8 ms |
| No expansion | 0.1583 | 0.0843 | 354.4 ms |
| No BM25 | 0.1417 | 0.0530 | 271.1 ms |
| No dense retrieval | 0.0833 | 0.0488 | 254.8 ms |
| No RRF; fixed route concatenation | 0.0583 | 0.0232 | 489.2 ms |

Transliteration, dense retrieval, and RRF have the largest positive contributions in these controls. Normalization and BM25 provide smaller gains. Controlled expansion is a negative result: removing it lowers Recall@10 slightly but raises MRR@10, so its current rule should be redesigned rather than defended as uniformly helpful. Reranking raises MRR@10 from 0.0750 to 0.1444 and Recall@10 from 0.1667 to 0.1833.

## Practicality

The 16,352 × 384 float32 embedding matrix is 25,116,800 bytes. Its cold CPU build, including embedding generation and serialization, took 2,546.3 seconds. QueryBridge without reranking averaged 444.0 ms (p95 656.2 ms). Depth-20 reranking averaged 16,397.0 ms in addition to retrieval and used approximately 2.52 GB resident memory. It improves early ranking but is unsuitable for an interactive CPU path at that depth; the measured depth-5 path remains the deployment candidate.

## Failure review

The audit contains 30 failed development queries, balanced across six observed categories: Roman spelling mismatch, excessive spelling noise, code-switching failure, named-entity mismatch, short/ambiguous query, and irrelevant retrieval. Each row includes the real query, gold passage ID, top retrieved passage and title, cause, affected system, and proposed improvement.

These categories are deterministic first-pass labels, not native-speaker judgments. The CSV marks every row `rule_assigned_requires_human_review`; paper and viva claims must use reviewed labels.

## Reproduction

After the measured Phase 2, Phase 5, and ablation detail files exist, one local command regenerates the robustness table, latency/resource table, 30-case audit, and both SVG figures:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts\generate_phase6_outputs.py
```
