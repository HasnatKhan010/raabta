# Raabta React interface

This local Vite interface calls the FastAPI service at `http://127.0.0.1:8000` by default. It shows the grounded answer, exact Urdu evidence, source, converted query, every completed pipeline stage, per-route candidate counts, every evidence gate with observed and required values, candidate routes, relevance confidence, acceptance or rejection reasons, latency, and optional Research Mode comparison.

The “Live Urdu Wikipedia” option is off by default. Enabling it sends the converted query to Wikipedia only when the local corpus cannot provide a validated answer.

Dependencies live only in `frontend/node_modules` and can be removed safely. On the main PC, run `pnpm install --frozen-lockfile` inside this folder to recreate them.

Start the API first, then run `pnpm dev` here. Set `VITE_API_BASE` only if the local API uses a different address.
