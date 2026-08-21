# Quick Streamlit deployment

The Streamlit interface is an additional deployment option. It does not replace the existing FastAPI backend or React frontend, and it uses the same `RaabtaEngine` and evidence-validation logic.

## Fastest local demonstration

Use the prepared project copy because it already contains the local corpus, embeddings, and model caches:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\start_streamlit.ps1
```

Streamlit opens its local URL, normally `http://localhost:8501`. Stop it with `Ctrl+C`. All packages remain inside `.venv`.

## Streamlit Community Cloud

Use repository `HasnatKhan010/raabta`, branch `main`, and entrypoint `streamlit_app.py`.

The GitHub repository intentionally excludes approximately 1.1 GB of model caches and generated research artifacts. A normal Community Cloud clone therefore cannot run the full local engine by itself. The recommended hosted arrangement is:

1. Deploy the existing FastAPI service on infrastructure that has the prepared `data/` and `artifacts/` folders.
2. In Streamlit Community Cloud, add this secret:

   ```toml
   RAABTA_API_URL = "https://your-raabta-api.example.com"
   ```

3. Deploy `streamlit_app.py`. The Streamlit process becomes a lightweight UI and sends queries to the same FastAPI pipeline.

Alternatively, make the required data/model artifacts available to the Streamlit deployment through an approved artifact build or Git LFS workflow. Do not commit secrets or silently substitute a toy model. When neither a remote API nor all local artifacts are available, the app explains the missing setup and refuses to fabricate a result.

## Deployment behavior

- The expensive local engine is cached once with `st.cache_resource`.
- Research mode and the optional live Urdu Wikipedia fallback remain available.
- Live fallback stays off by default and shows a privacy warning.
- The interface displays the exact answer/evidence, source, confidence, validation gates, query views, retrieval routes, top candidates, and timing.
- `RAABTA_API_URL` can be set through an environment variable locally or Streamlit secrets when hosted.
