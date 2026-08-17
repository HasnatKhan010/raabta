# Phase 9 — React interface and Research Mode

The local interface implements the complete user-visible pipeline without Streamlit. It is a responsive React/Vite application designed around one primary action: asking a Roman-Urdu, Urdu, or mixed-English question.

## What the user sees

- A concise evidence-grounded answer in Urdu.
- Exact source sentences, with passage rank and semantic similarity.
- Clickable Urdu Wikipedia title and URL.
- Original, normalized Roman, Urdu-script, and retrieval-oriented QueryBridge variants, including rejected duplicates.
- The top five fused results and their BM25/dense contributing routes.
- Honest score wording: raw ranking scores are never presented as probabilities.
- Retrieval, evidence-selection, and total latency.
- Research Mode comparisons for Direct Dense, Single Transliteration, Standard Hybrid, and Raabta.

For arbitrary user questions, Research Mode displays `NOT PROVIDED` for gold rank because no gold evidence exists. The application never invents a relevance label. The comparison endpoint can display a rank or `NOT RETRIEVED` when a verified gold passage ID is explicitly supplied.

## Local operation

Start the backend in one terminal:

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Start the interface in another terminal:

```powershell
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

Then open `http://127.0.0.1:5173`. The first query is slower because the backend loads the corpus and local model lazily.

`frontend/node_modules` and `frontend/dist` are excluded from Git and may be deleted at any time. Copy the source and `pnpm-lock.yaml` to the main PC, then recreate dependencies with the frozen lockfile.

## Validation

The TypeScript compiler and Vite production build complete successfully. The final assets are approximately 197 kB JavaScript and 8 kB CSS before gzip. Backend integration uses an explicit local CORS allowlist rather than a wildcard.
