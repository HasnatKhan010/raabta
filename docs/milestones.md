# Milestone checklist

## Phase 0 — complete

- [x] Inspect repository
- [x] Record gap analysis
- [x] Verify primary dataset and supporting dataset pages/licenses
- [x] Verify dense encoder and reranker artifacts
- [x] Record CPU and dependency decisions
- [x] Add configuration and repository skeleton

## Phase 1 — data

- [x] Define article, passage, and diagnostic data contracts
- [x] Preserve raw and normalized article text
- [x] Implement deterministic selection/domain metadata
- [x] Implement configurable overlapping passage chunks
- [x] Add explicit download/build commands
- [x] Validate locally on a fixture corpus
- [x] Download and inspect the real 4,000-article subset (explicit network/storage step)
- [x] Download and inspect the bounded 30,000-row Roman-Urdu supporting slice
- [x] Create a deterministic 180-item, six-domain manual annotation queue
- [x] Create and evidence-verify 180 provisional questions with Codex as annotator
- [ ] Obtain independent native-speaker review before final-paper claims
- [x] Freeze the 120/60 development/test split before tuning

## Phase 2 — baselines (complete provisionally)

- [x] BM25 retriever with Unicode tokenization
- [x] Exact normalized dense-retrieval implementation
- [x] Deterministic one-best transliteration baseline
- [x] Equal-weight RRF for the conventional hybrid baseline
- [x] Recall@K, MRR@10, and nDCG@10 implementations
- [x] Offline unit tests using a fake encoder
- [x] Download the pinned E5 model into the project-local cache
- [x] Build and checksum the 16,352-passage embedding index
- [x] Run traceable qualitative smoke queries against all three real baselines
- [x] Run the three baselines on Codex-verified development annotations
- [x] Freeze baseline definitions and report explicitly provisional real metrics

## Later phases

- [x] Run three baselines on the provisional Codex-verified development split
- [x] Freeze provisional baseline definitions; final reporting still awaits independent review
- [x] Phase 3: controlled QueryBridge with drift audit
- [x] Phase 4: deduplication, RRF, route trace
- [x] Phase 5: pinned-code CPU reranker benchmark and full development evaluation
- [x] Phase 6: development robustness, retrieval-stage ablations, latency, and 30-case provisional error analysis
- [ ] Final-paper Phase 6: native review plus reranker-retained controls for all six retrieval ablations
- [x] Phase 7: extractive grounded answer, exact source citation, trace, and abstention
- [x] Phase 8: FastAPI backend with health, query, compare, source, and config endpoints
- [x] Phase 9: responsive React/Vite frontend and honest Research Mode comparison
- [x] Phase 10: clean-room package test, portability audit, notebook execution, and reproduction checks
- [x] Phase 11: provisional development paper, full README, figures, and viva preparation
- [ ] Final scientific release: independent native-speaker review, configuration sign-off, and one-time locked-test evaluation
