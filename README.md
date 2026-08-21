<p align="center">
  <strong lang="ur" dir="rtl">رابطہ</strong>
</p>

<h1 align="center">RAABTA</h1>

<p align="center">
  <strong>Accurate, evidence-first search for Roman-Urdu questions</strong><br>
  <em>Script-aware retrieval over Urdu knowledge sources</em>
</p>

<p align="center">
  <a href="https://github.com/HasnatKhan010/raabta/actions/workflows/ci.yml"><img src="https://github.com/HasnatKhan010/raabta/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white" alt="Python 3.11 and 3.12">
  <img src="https://img.shields.io/badge/Tests-51%20passing-2E7D32" alt="51 tests passing">
  <img src="https://img.shields.io/badge/Runtime-CPU--only-brightgreen" alt="CPU-only runtime">
  <img src="https://img.shields.io/badge/UI-React%20%2B%20Vite-61DAFB?logo=react&logoColor=black" alt="React and Vite">
</p>

---

## What Raabta does

Roman Urdu is commonly typed with Latin characters, while much useful information is written in Urdu script. Informal spelling makes the problem harder: the same name can be typed in several different ways.

Raabta connects those two forms. It converts and expands the user’s query, searches the local Urdu corpus through complementary retrieval routes, reranks the strongest candidates, and returns an exact sentence from a validated source. If the evidence is weak or does not answer the requested relation, it abstains instead of showing an unrelated result.

> **Research question:** Can script-aware multi-query reformulation improve retrieval for noisy Roman-Urdu questions over Urdu-script knowledge bases compared with direct, single-transliteration, and standard hybrid retrieval?

<p align="center">
  <img src="docs/raabta_interface.jpg" alt="Raabta interface showing a grounded Urdu result and its evidence" width="760">
</p>
<p align="center"><em>Every answer includes the source, evidence, decision checks, retrieval routes, and timing.</em></p>

## Quick start

### Prepared assignment folder

The prepared project copy already contains the corpus, embeddings, local model files, and built interface.

Requirements:

- Windows with PowerShell
- Python 3.11 or 3.12
- Internet access during the first setup only, for pinned Python packages

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start_raabta.ps1
```

Raabta opens at [http://127.0.0.1:5173](http://127.0.0.1:5173). Stop it with:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_raabta.ps1
```

All installed Python packages remain inside `.venv`. Deleting that folder removes the project environment without affecting global Python.

### Quick Streamlit demo

The original FastAPI + React application remains the full deployment. For a faster one-command demonstration using the same retrieval and evidence engine, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\start_streamlit.ps1
```

The local Streamlit URL is normally [http://localhost:8501](http://localhost:8501). For Streamlit Community Cloud, use `streamlit_app.py` as the entrypoint and configure `RAABTA_API_URL` to a deployed instance of the existing FastAPI backend. See [Streamlit deployment](docs/streamlit_deployment.md) for the artifact and secrets requirements.

### Fresh GitHub clone

Large data, embeddings, model weights, and `frontend/dist` are intentionally not stored in Git. A fresh clone therefore requires the data pipeline and a frontend build:

```powershell
git clone https://github.com/HasnatKhan010/raabta.git
cd raabta
powershell -ExecutionPolicy Bypass -File .\setup.ps1

.\.venv\Scripts\Activate.ps1
python scripts\download_data.py
python scripts\build_corpus.py
python scripts\build_transliteration_lexicon.py
python scripts\build_dense_index.py

pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
powershell -ExecutionPolicy Bypass -File .\start_raabta.ps1
```

The frontend build requires Node.js and pnpm. The prepared assignment folder does not require either because it already contains the built interface.

## How the current system works

```text
Roman-Urdu question
        |
        v
QueryBridge
  - original query
  - normalized Roman Urdu
  - Urdu-script conversion
  - controlled retrieval form
        |
        +----------------------+-----------------------+
        |                      |                       |
        v                      v                       v
Urdu BM25 search      Multilingual dense search   Romanized-title search
(title boosted)          (E5-small)                (character 2–4 grams)
        |                      |                       |
        +----------------------+-----------------------+
                               |
                               v
                 Weighted reciprocal-rank fusion
                               |
                               v
              Multilingual reranker over title + passage
                               |
                               v
       Source alignment + relevance + relation/evidence checks
                         /                     \
                        v                       v
             Exact sourced answer       Clear abstention
                                                 |
                                    optional user-enabled
                                    Urdu Wikipedia fallback
```

The romanized-title route is the main accuracy improvement. It romanizes each Urdu article title with pinned `uroman` rules and uses character-level matching so that missing vowels, abbreviations, and informal entity spellings can still reach the correct article. Only one lead passage per matched article enters this route, preventing duplicate chunks from overwhelming the candidate list.

## Accuracy improvement

The regression check uses the same 120 frozen development questions before and after the title route was added. The separate 60-question test split remains unused.

| Development retrieval pipeline | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Previous application retrieval | 0.075 | 0.117 | 0.192 | 0.101 | 0.122 |
| **Current retrieval with romanized-title route** | **0.392** | **0.875** | **0.983** | **0.583** | **0.680** |

Recall@10 improved by **0.792 absolute**, from 0.192 to 0.983. This is a retrieval measurement on a title-oriented development set—not a claim that 98.3% of unrestricted questions receive a correct final answer.

Earlier baseline and ablation measurements are retained in [Development results](docs/development_results.md) and [Phase 6 analysis](docs/phase6_analysis.md).

## How unrelated answers are prevented

Retrieving the right article is necessary but not sufficient. Before displaying an answer, Raabta checks:

1. whether the reranker score clears the relevance threshold;
2. whether meaningful query content aligns with the selected source;
3. whether the evidence sentence clears the semantic-similarity threshold;
4. whether the sentence contains the requested relation, such as birth, death, price, or current capital;
5. whether a current question is being answered by an outdated historical statement;
6. whether the text is navigation, references, templates, or a generic list description; and
7. whether the extracted sentence comes from the exact source that passed validation.

A failed check produces a visible abstention reason. The system does not generate a replacement fact.

## What the interface explains

For each query, the frontend shows:

- the current pipeline stage and final decision;
- original, normalized, and Urdu-script query forms;
- accepted and rejected QueryBridge variants;
- candidates contributed by BM25, dense, and romanized-title routes;
- reranker relevance, content overlap, title match, and evidence thresholds;
- exact evidence, article title, passage identifier, and source link;
- candidate passages that were checked but rejected;
- local, reranking, validation, and optional live-search latency; and
- why an answer was accepted or why the system abstained.

**Research Mode** can also compare Direct Dense, Single Transliteration + BM25, Standard Hybrid, and the full Raabta pipeline for the same query.

## Local and live search

Normal searches stay on the PC and use the bounded local corpus. If the local result fails validation, the user can explicitly enable **Live Urdu Wikipedia fallback** and retry.

The live option:

- is off by default;
- sends the converted query to Urdu Wikipedia only when enabled;
- passes returned passages through the same reranking and validation checks; and
- is intended for encyclopedic coverage, not shopping prices or breaking news.

## Data and models

| Component | Assignment configuration |
|---|---|
| Urdu corpus | 4,000 Wikipedia articles from the frozen `20231101.ur` snapshot |
| Passage collection | 16,352 passages; 150-token windows with 30-token overlap |
| Diagnostic set | 180 evidence-linked questions: 120 development and 60 locked test |
| Dense encoder | `intfloat/multilingual-e5-small`, 384 dimensions |
| Reranker | `Alibaba-NLP/gte-multilingual-reranker-base`, top 20 candidates |
| Title romanizer | `uroman==1.3.1.1` |
| Retrieval | Unicode BM25 + exact dense search + romanized-title matching + weighted RRF |
| Runtime | CPU-only |

Dataset and model revisions are pinned in [configs/default.yaml](configs/default.yaml). Artifact checksums are recorded under `artifacts/metadata` in a complete project copy.

## Project layout

```text
raabta/
├── backend/                 FastAPI application and response models
├── frontend/                React/TypeScript interface
├── streamlit_app.py         Quick Streamlit interface using the same engine/API
├── src/raabta/
│   ├── querybridge/         Query normalization and script conversion
│   ├── retrieval/           BM25, dense, title matching, fusion, live fallback
│   ├── reranking/           Multilingual cross-encoder
│   ├── evidence/            Extraction, relevance checks, and abstention
│   ├── evaluation/          Recall, MRR, and nDCG metrics
│   └── data/                Data contracts and loaders
├── configs/                 Frozen project configuration
├── data/                    Local corpora and diagnostic data
├── artifacts/               Embeddings, indexes, metadata, and local models
├── reports/                 Measured tables, figures, and failure analysis
├── notebooks/               Seven executed analysis notebooks
├── paper/                   Assignment report source and compiled PDF
├── scripts/                 Data, evaluation, audit, and report builders
├── tests/                   Automated test suite
├── setup.ps1                Create the isolated Python environment
├── start_raabta.ps1         Start API and built frontend
└── stop_raabta.ps1          Stop both local services
```

## API

The backend is available at `http://127.0.0.1:8000`. Interactive API documentation is available at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Check application and artifact availability |
| `POST` | `/api/query` | Run retrieval, reranking, evidence validation, and optional live fallback |
| `POST` | `/api/compare` | Compare the four retrieval systems |
| `GET` | `/api/source/{passage_id}` | Return the exact stored source passage |
| `GET` | `/api/config` | Show active non-probabilistic project settings |

Example request:

```json
{
  "query": "pakistan ka capital kya hai",
  "research_mode": false,
  "live_search": false
}
```

## Development checks

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src backend scripts tests
pnpm --dir frontend build
.\.venv\Scripts\python.exe scripts\audit_portability.py
```

Current verification:

- 47 automated tests pass;
- Python lint passes;
- the React production build passes;
- the portability audit passes;
- all seven detailed notebooks execute with visible outputs and 11 linked visualizations;
- the diagnostic split remains 120 development / 60 locked test; and
- all inspected evaluation reports confirm zero locked-test queries used.

## Documentation

| Document | Contents |
|---|---|
| [Executed assignment notebooks](notebooks/README.md) | Detailed Parts 1–10 analysis, results, visualizations, and deployment linkage |
| [IEEE research paper](paper/main.pdf) | Complete six-page Part 11 paper with LaTeX source |
| [Implementation plan](docs/implementation_plan.md) | Architecture and implementation decisions |
| [Accuracy hardening](docs/accuracy_hardening.md) | Title retrieval and answer-validation improvements |
| [Development results](docs/development_results.md) | Current and earlier retrieval measurements |
| [Phase 6 analysis](docs/phase6_analysis.md) | Robustness, ablations, latency, and failure findings |
| [Grounded QA](docs/phase7_grounded_qa.md) | Extractive-answer design |
| [Frontend validation](docs/phase9_frontend.md) | Interface behavior |
| [Streamlit deployment](docs/streamlit_deployment.md) | Quick local demo and Community Cloud setup |
| [Portability validation](docs/phase10_validation.md) | Reproducibility checks |

## Assignment scope and limitations

- The reported scores are development-set measurements; the locked test split is not used.
- Recall@10 measures whether relevant evidence appears in the first ten results, not final-answer correctness.
- The diagnostic questions are title-oriented and do not represent every Roman-Urdu information need.
- The 4,000-article local corpus cannot cover every topic.
- Live Wikipedia fallback is not a dependable source for current prices or breaking news.
- Wikipedia attribution and dataset license requirements must be preserved when data is shared.

## Author

**Hasnat Khan**

This repository is the assignment project copy. Source-dataset terms and attribution notes are documented in [data/README.md](data/README.md).
