# Accuracy hardening

This pass targets high precision: retrieve the correct source more often, show only a sentence from a validated source, and abstain when the required fact is not present.

## Measured retrieval change

The check uses the 120 `project_verified` development questions only. The 60 locked test questions remain unused.

| Development retrieval pipeline | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
|---|---:|---:|---:|---:|
| Previous local QueryBridge pipeline | 0.075 | 0.117 | 0.192 | 0.101 |
| With romanized-title retrieval | 0.392 | 0.875 | 0.983 | 0.583 |

The diagnostic set is title-oriented. These figures are assignment regression measurements, not an answer-accuracy percentage and not a guarantee for unrestricted questions.

## Accuracy controls

1. Romanize all 4,000 Urdu article titles with pinned `uroman` rules.
2. Match noisy Roman text with character 2–4 grams so missing vowels and informal spelling remain searchable.
3. Keep one lead passage per article in this route to prevent duplicate chunks from flooding the candidate list.
4. Fuse this route with Urdu BM25 and multilingual dense retrieval.
5. Rerank title plus passage text, rather than passage text alone.
6. Permit answer extraction only from the exact top source that passed source-alignment checks.
7. Require the requested relation: birth wording for birth dates, death wording for death dates, currency plus amount for prices, and a current capital statement for a current-capital question.
8. Reject navigation text, reference sections, and generic list descriptions.
9. Prefer the lead sentence for broad “what is / tell me about” questions.
10. Explain every route, stage, gate, threshold, rejection, source, and latency component in the API response and UI.

## Known boundary

The bundled local corpus contains 4,000 Urdu Wikipedia articles, so it cannot answer every topic or provide dependable current commercial prices. The optional live Urdu Wikipedia fallback broadens encyclopedic coverage, but it is not a general shopping or breaking-news source. Unsupported questions must abstain rather than guess.
