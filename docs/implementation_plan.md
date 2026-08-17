# RAABTA implementation plan

The build order follows the master specification. Each phase has a testable exit condition; downstream work does not overwrite or tune against the final test split.

1. **Phase 0 — foundation:** verify sources and model artifacts, record revisions, resolve dependency strategy, create the repository structure and milestones.
2. **Phase 1 — data:** stream/download explicit subsets, preserve raw text, normalize conservatively, assign project domain labels, chunk articles, retain complete passage provenance, and define the diagnostic schema.
3. **Phase 2 — baselines:** implement direct E5 dense retrieval, one deterministic Urdu conversion plus BM25, and conventional BM25+dense RRF. Freeze baseline definitions before QueryBridge.
4. **Phase 3 — QueryBridge:** produce 2–4 controlled variants with method/reason metadata and semantic-drift decisions. Gold evidence is never an input.
5. **Phase 4 — fusion:** deduplicate by passage ID, apply transparent equal-weight RRF, and retain per-route ranks.
6. **Phase 5 — reranking:** benchmark the pinned multilingual reranker on CPU over only 20 candidates. Keep it optional if memory or latency is impractical and document the result.
7. **Phase 6 — evaluation:** tune only on development data, freeze configuration, then calculate Recall@1/5/10, MRR@10, nDCG@10, robustness breakdowns, ablations, failures, and resource usage.
8. **Phase 7 — grounded QA:** select exact supporting sentences and abstain below a development-selected support threshold.
9. **Phase 8 — backend:** expose the tested pipeline through FastAPI schemas and endpoints without route-level business logic.
10. **Phase 9 — frontend:** build the React/Vite evidence interface and factual Research Mode comparison.
11. **Phase 10 — hardening:** clean-environment install, unit/integration tests, notebook execution, and reproducibility audit.
12. **Phase 11 — communication:** write the paper, README completion, actual result figures/tables, error analysis, and viva answers.

## Leakage policy

Diagnostic records will receive an immutable split before tuning. Transformations, chunk sizes, top-k, thresholds, and route weights are chosen only on development data. The test set is run only after decisions are frozen. Query generation never receives gold article, passage, evidence, or answer fields.

