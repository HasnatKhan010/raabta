# Raabta React interface

This local Vite interface calls the FastAPI service at `http://127.0.0.1:8000` by default. It shows the grounded answer, exact Urdu evidence, source, QueryBridge variants, retrieval routes, scores, latency, and optional Research Mode comparison.

Dependencies live only in `frontend/node_modules` and can be removed safely. On the main PC, run `pnpm install --frozen-lockfile` inside this folder to recreate them.

Start the API first, then run `pnpm dev` here. Set `VITE_API_BASE` only if the local API uses a different address.
