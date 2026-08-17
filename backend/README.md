# Raabta FastAPI backend

The backend exposes the complete local retrieval and evidence-grounded answer pipeline. Models, data, embeddings, and the transliteration lexicon are loaded only from project-local paths. The depth-20 reranker remains offline-only because its measured CPU latency is unsuitable for the interactive endpoint.

## Run

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the generated API interface.

## Endpoints

- `GET /health` checks artifact availability without forcing model loading.
- `POST /api/query` runs QueryBridge retrieval and extractive QA. `research_mode: true` includes baseline comparison data.
- `POST /api/compare` returns the four retrieval rankings. A supplied `gold_passage_id` produces real gold ranks or `NOT RETRIEVED`; no gold is inferred.
- `GET /api/source/{passage_id}` returns the exact source passage or HTTP 404.
- `GET /api/config` reports the active non-probabilistic engineering settings.

The first query loads the local encoder and corpus into memory, so it is slower than later requests.
