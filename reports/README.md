# Experiment reports

This folder contains the measured development artifacts used by the notebooks and IEEE paper:

- `tables/`: baseline, QueryBridge, title-route, reranker, robustness, latency, grounded-QA, and portability results;
- `figures/`: reproducible SVG visualizations linked from the executed notebooks;
- `error_analysis/`: the traceable 30-case failure audit.

All retrieval scores are development-set measurements. The locked 60-question test partition remains unused, and Recall@10 must not be described as unrestricted answer accuracy. Regenerate the detailed notebooks and their visualizations with `scripts/generate_notebooks.py` followed by `scripts/execute_notebooks.py`.

