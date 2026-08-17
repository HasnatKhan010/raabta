# Repository gap analysis

Assessment date: 2026-08-16.

At inspection, the repository contained only an isolated Python environment and setup notes. It had no RAABTA source code, data contracts, corpus, experiments, tests, backend, frontend, notebooks, paper, or measured results.

| Specification area | Initial state | Phase / action |
|---|---|---|
| Reproducible configuration | Missing | Phase 0: added versioned YAML configuration |
| Dataset acquisition and licensing | Missing | Phase 0 verified sources; Phase 1 uses explicit streaming scripts |
| Urdu preprocessing and passage metadata | Missing | Phase 1 implementation and fixture tests |
| Diagnostic evaluation set | Missing | Phase 1 schema/template; manual annotation remains required |
| Three retrieval baselines | Missing | Phase 2, after corpus validation |
| QueryBridge | Missing | Phase 3, after baselines freeze |
| RRF and route trace | Missing | Phase 4 |
| Multilingual reranker | Missing | Phase 5, conditional on CPU benchmark |
| Metrics, robustness, ablations, latency | Missing | Phase 6; no values may be invented |
| Grounded extractive QA and abstention | Missing | Phase 7 |
| FastAPI backend | Missing | Phase 8 |
| React/Vite frontend | Missing | Phase 9, deliberately not started in Phase 0 |
| Full tests and clean-room validation | Missing | Tests begin per phase; complete in Phase 10 |
| Paper, notebooks, viva material | Missing | Phase 11 after real results exist |

## Research boundary

RAABTA is not a classifier and not a generic chatbot. The independent variable is the retrieval strategy/query representation; supervision is query-to-passage relevance. The exact research question in `README.md` remains unchanged.

## Important unresolved work

- The 150–200 question Raabta Diagnostic Set requires manual, native-language verification; generating it automatically would violate the specification.
- Domain labels are absent from the Wikimedia record schema. Phase 1 therefore uses a documented deterministic heuristic label for subset balancing; these are project metadata, not official Wikipedia categories.
- Model support for Urdu must be measured on RAABTA data. A multilingual model card is availability evidence, not proof of Urdu effectiveness.
- A repository license cannot be selected on the student's behalf without confirming publication intentions. It remains explicitly TBD; dataset licenses are documented separately.
- Final paper results, figures, thresholds, and claims must wait for the frozen evaluation run.

