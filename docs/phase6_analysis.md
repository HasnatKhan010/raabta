# Phase 6 — development evaluation and analysis

The original Phase 6 evaluation used 120 project-verified development records and zero locked-test records. Its findings motivated the later accuracy-hardening pass.

## Original robustness finding

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

The weak entity, informal-spelling, and abbreviation scores showed that semantic retrieval alone was not reliably finding the correct article.

## Retrieval controls

| Retrieval configuration | Recall@10 | MRR@10 | Mean latency |
|---|---:|---:|---:|
| Full retrieval, no reranker | 0.1667 | 0.0750 | 425.2 ms |
| No normalization | 0.1500 | 0.0715 | 402.9 ms |
| No transliteration | 0.0667 | 0.0253 | 335.8 ms |
| No expansion | 0.1583 | 0.0843 | 354.4 ms |
| No BM25 | 0.1417 | 0.0530 | 271.1 ms |
| No dense retrieval | 0.0833 | 0.0488 | 254.8 ms |
| No RRF; fixed route concatenation | 0.0583 | 0.0232 | 489.2 ms |

Transliteration, dense retrieval, and RRF made the largest positive contributions. Controlled expansion produced a mixed result and is not presented as uniformly helpful. Depth-20 reranking raised MRR@10 from 0.0750 to 0.1444 but added about 16.4 seconds on CPU, making it unsuitable for the normal interactive path.

## Accuracy-hardening result

The current application adds a romanized-title retrieval route and lead-passage restriction. On the same development questions, Recall@10 improved from 0.1917 to 0.9833, Recall@5 from 0.1167 to 0.8750, and MRR@10 from 0.1014 to 0.5830 before cross-encoder reranking.

The answer layer then applies relation-aware evidence gates. For example, a birth-date question requires birth wording, a current-capital question requires a current-capital statement, and a price question requires both currency and an amount. Broad definition questions prefer the lead sentence. This reduces the chance that the top passage is converted into a plausible but unrelated response.

## Trace and failure behavior

The API and interface expose normalized and converted query views, every retrieval route, candidate counts, reranking state, confidence, gate decisions, source title, evidence text, abstention reason, and latency. The 30-case failure audit remains available in `reports/error_analysis/failures_30.csv`.

## Reproduction

Run the evaluation generators inside the project virtual environment:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts\generate_phase6_outputs.py
```
