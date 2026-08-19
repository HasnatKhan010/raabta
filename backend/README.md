# Raabta FastAPI backend

The backend exposes the complete retrieval and evidence-grounded answer pipeline. Models, data, embeddings, and the transliteration lexicon are loaded from project-local paths. A character-level romanized-title route searches one lead passage per article alongside BM25 and multilingual dense retrieval. Interactive queries then use the multilingual reranker plus source alignment, sentence similarity, requested-relation, current-versus-historical, and boilerplate checks. The extractor is restricted to the exact top source that passed validation. When those checks fail, the API abstains rather than returning an unrelated sentence.

`live_search` is an explicit per-query opt-in. When true, an unsupported local query may be sent to Urdu Wikipedia and its retrieved passages are passed through the same reranking and evidence checks. It remains false by default so normal use stays local.

## Run

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:PYTHONPATH = "src;."
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for the generated API interface.

## Endpoints

- `GET /health` checks artifact availability without forcing model loading.
- `POST /api/query` runs QueryBridge retrieval and extractive QA. `live_search: true` enables the Urdu Wikipedia fallback, and `research_mode: true` includes baseline comparison data.
- `POST /api/compare` returns the four retrieval rankings. A supplied `gold_passage_id` produces real gold ranks or `NOT RETRIEVED`; no gold is inferred.
- `GET /api/source/{passage_id}` returns the exact source passage or HTTP 404.
- `GET /api/config` reports the active non-probabilistic engineering settings.

The first query loads the local encoder and corpus into memory, so it is slower than later requests.
