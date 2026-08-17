# Raabta viva preparation

## Two-minute opening

Raabta addresses a practical script mismatch. Many users type Urdu in Latin characters, while useful knowledge is stored in Urdu script. Direct lexical search therefore misses relevant passages even when the meaning is clear. My research question is whether several controlled, meaning-preserving query views can bridge this gap more effectively than direct dense retrieval, one-best transliteration, or a conventional hybrid baseline.

The system preserves the original Roman-Urdu query, normalizes noise, produces an Urdu-script view and conservative expansions, retrieves each view through BM25 and multilingual dense search, fuses the routes with reciprocal-rank fusion, and optionally reranks a shallow candidate set. It then returns an exact evidence sentence or abstains.

I built a traceable corpus of 4,000 Urdu Wikipedia articles and 16,352 passages, plus a student-curated 180-question diagnostic set with a frozen 120-question development split and a locked 60-question test split. On development data, QueryBridge reached Recall@10 of 0.167 versus 0.092 for the strongest frozen baseline. Depth-20 reranking raised Recall@10 to 0.183 and MRR@10 to 0.144, but cost about 16.4 seconds on CPU, so it remains an optional quality tier.

The honest limitation is that independent native-speaker review is still pending. I have not opened the locked test split. The defensible conclusion is therefore a development result: script-aware multi-query retrieval improves access under the frozen development protocol, while abbreviations, entities, informal spellings, and CPU reranking cost remain important open problems.

## Likely questions and concise answers

### Why not transliterate once and use BM25?

One-best transliteration is brittle under informal spelling and ambiguity. Its development Recall@10 was 0.025. Keeping several controlled views and combining lexical and semantic routes reached 0.167 before reranking.

### Why retain the original Roman-Urdu query?

It anchors the user's wording and can match Latin-script names or code-switched terms. Removing a view only after deduplication or drift checks is safer than assuming transliteration is always correct.

### Why use reciprocal-rank fusion?

BM25 and dense scores are on different scales. RRF combines ranked evidence without pretending the raw scores are calibrated probabilities, and it leaves an auditable route trace.

### What is the strongest ablation result?

Removing fusion lowered Recall@10 from 0.167 to 0.058, removing transliteration lowered it to 0.067, and removing dense retrieval lowered it to 0.083. These components carry most of the retrieval gain.

### Did every component help?

No. Removing expansion slightly increased MRR from 0.075 to 0.084 while reducing Recall@10 from 0.167 to 0.158. I report that mixed result rather than claiming universal improvement.

### Why is the absolute Recall@10 still low?

The diagnostic questions deliberately include noisy, short, entity-heavy, ambiguous, code-switched, and abbreviated inputs. The robustness analysis shows that clean queries reach 0.500 Recall@10, while abbreviated queries reach 0.000. This identifies where future modeling effort is needed.

### Is the reranker practical?

Not for a low-latency CPU-only interaction at the measured depth. It improves Recall@10 to 0.183 and MRR@10 to 0.144 but averages about 16.4 seconds. The application therefore uses QueryBridge as the interactive tier and treats reranking as optional.

### How do you prevent hallucination?

The answer layer is extractive. It returns text found in a cited passage, includes the source and rank, and abstains below the support threshold. It does not generate an unsupported free-form answer.

### How did you prevent test leakage?

The 120/60 split was frozen before tuning. Query generation never receives gold passage or answer fields. All displayed metrics are development-only, and the locked test split remains unused until independent review and final configuration sign-off.

### What would make the work ready for a final scientific claim?

Independent native-speaker validation of the diagnostic annotations and failure labels, configuration sign-off, and a single locked-test run using the frozen pipeline. The test result should then be reported once without further tuning.

### What is the main contribution?

Not the first Roman-Urdu IR benchmark. The contribution is a reproducible, end-to-end evaluation of controlled script-aware query views, complementary retrieval routes, transparent fusion, optional reranking, and evidence-grounded answer behavior.

## Numbers to remember

- 4,000 articles; 16,352 passages
- 180 questions; 120 development; 60 locked test
- Recall@10: dense 0.092; QueryBridge 0.167; reranked 0.183
- MRR@10: QueryBridge 0.075; reranked 0.144
- Latency: dense 51.8 ms; QueryBridge 444 ms; reranker 16.4 s
- 32 tests; seven executed notebooks; 30 audited failures

## Claim guardrails

- Say "development result," not "final benchmark result."
- Say "student-curated diagnostic set," not "representative benchmark."
- Say "improves on this frozen development protocol," not "solves Roman-Urdu retrieval."
- Say the failure categories are provisional until native-speaker review.
- State the reranker's CPU cost whenever presenting its accuracy gain.
