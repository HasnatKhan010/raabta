# Development results

Run date: 2026-08-20. All measurements use the 120 `project_verified` development questions. The locked 60-question test split was not used.

## Current application retrieval

| Development pipeline | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Previous QueryBridge retrieval | 0.0750 | 0.1167 | 0.1917 | 0.1014 | 0.1219 |
| QueryBridge + romanized-title route | **0.3917** | **0.8750** | **0.9833** | **0.5830** | **0.6796** |

The title route raises Recall@10 by 0.7916 absolute on this title-oriented development set. It romanizes all 4,000 Urdu article titles with pinned `uroman` rules, matches noisy Roman text with character 2–4 grams, and contributes only the lead passage from each matched article. This makes informal spellings and missing vowels much less likely to hide the correct source.

These figures measure retrieval, not final answer accuracy. The answer layer separately checks source alignment, query overlap, the requested relation, and evidence shape. If those gates fail, the interface explains the rejection and abstains instead of displaying unrelated text.

## Earlier system comparison

| System | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 | Mean latency |
|---|---:|---:|---:|---:|---:|---:|
| Direct Dense | 0.0500 | 0.0833 | 0.0917 | 0.0615 | 0.0686 | 51.4 ms |
| Single Transliteration + BM25 | 0.0000 | 0.0167 | 0.0250 | 0.0074 | 0.0116 | 59.6 ms |
| Standard Hybrid | 0.0250 | 0.0667 | 0.0917 | 0.0456 | 0.0565 | 94.1 ms |
| QueryBridge + BM25 + Dense + RRF | 0.0500 | 0.1000 | 0.1667 | 0.0750 | 0.0959 | 444.0 ms |
| QueryBridge + Reranker (depth 20) | 0.1250 | 0.1750 | 0.1833 | 0.1444 | 0.1540 | 16,947.6 ms* |

\* Mean retrieval (550.6 ms) plus reranking (16,397.0 ms); model loading excluded.

The earlier comparison established that controlled query views, BM25, dense retrieval, RRF, and reranking were useful, but also exposed poor title/entity matching. The current application retains those routes and adds the romanized-title route plus strict answer validation.

## Practical boundary

The local corpus contains 4,000 Urdu Wikipedia articles and cannot answer every topic or dependable current shopping-price question. Live Urdu Wikipedia search is optional and off by default. Unsupported questions must produce a visible abstention reason rather than a guessed answer.

