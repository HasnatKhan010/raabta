# Assignment notebooks

The seven executed notebooks form one detailed, reproducible assignment workflow. They contain written justification before preprocessing or modeling, visible tables and outputs, linked SVG visualizations, fixed seed `20250816`, and explicit development/test safeguards.

| Notebook | Assignment coverage |
|---|---|
| `01_dataset_setup.ipynb` | Parts 1–3: problem formulation, five-paper literature review, research gap, public datasets, features, relevance target, provenance, and limitations |
| `02_eda_and_preprocessing.ipynb` | Parts 4–5: justification for every preprocessing step, corpus/query EDA, chunking comparison, visualizations, and modeling difficulties |
| `03_baseline_retrieval.ipynb` | Parts 6–7: three distinct baselines, split/validation/tuning strategy, metrics, reproducibility, hardware/software, results, and latency |
| `04_querybridge.ipynb` | Part 8: baseline limitation, literature-based improvement, QueryBridge, romanized-title matching, before/after results, and a worked trace |
| `05_ablation.ipynb` | Parts 8–9: component ablations, title-route control, visual comparison, interpretation, and limitations |
| `06_robustness.ipynb` | Part 9: all-model comparison, robustness, latency/resources, best-model conclusion, and trade-offs |
| `07_error_analysis.ipynb` | Parts 9–10: traceable failure cases, evidence safety, FastAPI/React/Streamlit deployment verification, and final limitations |

Part 10's full runnable application is implemented under `backend/` and `frontend/`, with `streamlit_app.py` providing an additional quick-deployment interface over the same engine or API. All three paths are validated and linked from Notebook 07 rather than duplicated inside a notebook. Part 11 is the LaTeX/PDF submission under `paper/`.

From the project root, regenerate and execute everything with:

```powershell
.\.venv\Scripts\python.exe scripts\generate_notebooks.py
.\.venv\Scripts\python.exe scripts\execute_notebooks.py
.\.venv\Scripts\python.exe scripts\audit_portability.py
```

The notebooks read frozen local data and measured reports instead of repeating multi-hour embedding and reranker jobs. Measurement-generation scripts remain under `scripts/`, and the locked 60-question test partition remains unused.
