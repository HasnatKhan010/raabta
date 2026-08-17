# Provisional development results

Run date: 2026-08-16. These are real measurements on 120 `codex_verified` development questions. The 60 test questions were not used. They are engineering evidence only, not final-paper results, because independent native-speaker review is pending.

| System | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Mean latency |
|---|---:|---:|---:|---:|---:|---:|
| Direct Dense | 0.0500 | 0.0833 | 0.0917 | 0.0615 | 0.0686 | 51.4 ms |
| Single Transliteration + BM25 | 0.0000 | 0.0167 | 0.0250 | 0.0074 | 0.0116 | 59.6 ms |
| Standard Hybrid | 0.0250 | 0.0667 | 0.0917 | 0.0456 | 0.0565 | 94.1 ms |
| QueryBridge + BM25 + Dense + RRF | 0.0500 | 0.1000 | 0.1667 | 0.0750 | 0.0959 | 444.0 ms |
| QueryBridge + Reranker (depth 20) | 0.1250 | 0.1750 | 0.1833 | 0.1444 | 0.1540 | 16,947.6 ms* |

\* Mean retrieval (550.6 ms) plus reranking (16,397.0 ms); model loading excluded.

## Interpretation

On this provisional development set, QueryBridge increased Recall@10 by 0.075 absolute over Direct Dense and Standard Hybrid, and improved MRR@10 over all three baselines. It accepted 3.467 variants per query on average. The improvement came with substantially higher latency because several variants independently traverse lexical and semantic routes.

The completed retrieval controls show that transliteration, dense retrieval, and RRF contribute most strongly on this development set. Controlled expansion is currently a negative result: removing it changed Recall@10 from 0.1667 to 0.1583 but improved MRR@10 from 0.0750 to 0.0843. The title-definition query construction, deterministic Romanization, initial 0.55 drift threshold, and lack of independent language review can all influence these measurements. No test-set result has been computed.

## Reranker feasibility

The pinned `Alibaba-NLP/gte-multilingual-reranker-base` weights use revision `a6258e9d2b1a11aa7bccdff9efde562bbca4393d`; its separately referenced custom code is pinned to `40ced75c3017eb27626c9d4ea981bde21a2662f4`. Depth-20 reranking materially improved early ranking on development data, but required 16.4 seconds per query and approximately 2.52 GB resident memory. It is retained for offline experiments. A depth-5 benchmark averaged 2.6–3.4 seconds and is the current deployment candidate, subject to further quality measurement.
