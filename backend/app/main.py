from __future__ import annotations

from pathlib import Path
from typing import Protocol

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.models import (
    CompareRequest,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SourceResponse,
)
from backend.app.service import RaabtaEngine

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ARTIFACTS = (
    ROOT / "data/processed/passages_150_30.jsonl",
    ROOT / "artifacts/embeddings/e5_small_150_30.npy",
    ROOT / "artifacts/metadata/transliteration_lexicon.json",
)


class Engine(Protocol):
    def query(self, query: str, research_mode: bool = False, live_search: bool = False) -> dict: ...
    def compare(self, query: str, gold_passage_id: str | None = None) -> dict: ...
    def source(self, passage_id: str) -> dict | None: ...


def create_app(engine: Engine | None = None) -> FastAPI:
    application = FastAPI(title="Raabta API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.state.engine = engine

    def get_engine(request: Request) -> Engine:
        if request.app.state.engine is None:
            request.app.state.engine = RaabtaEngine(ROOT)
        return request.app.state.engine

    @application.get("/health", response_model=HealthResponse)
    def health(request: Request) -> dict:
        return {
            "status": "ok",
            "engine_loaded": request.app.state.engine is not None,
            "artifacts_ready": all(path.is_file() for path in REQUIRED_ARTIFACTS),
        }

    @application.get("/api/config")
    def config() -> dict:
        return {
            "answer_mode": "extractive",
            "reranker_interactive": True,
            "live_wikipedia_default": False,
            "evidence_threshold": 0.70,
            "reranker_relevance_threshold": RaabtaEngine.minimum_reranker_score,
            "retrieval_candidate_depth": 20,
            "answer_source_depth": 1,
            "romanized_title_route": True,
            "offline_local_models": True,
        }

    @application.post("/api/query", response_model=QueryResponse)
    def query(payload: QueryRequest, request: Request) -> dict:
        return get_engine(request).query(payload.query, payload.research_mode, payload.live_search)

    @application.post("/api/compare")
    def compare(payload: CompareRequest, request: Request) -> dict:
        return get_engine(request).compare(payload.query, payload.gold_passage_id)

    @application.get("/api/source/{source_id}", response_model=SourceResponse)
    def source(source_id: str, request: Request) -> dict:
        result = get_engine(request).source(source_id)
        if result is None:
            raise HTTPException(status_code=404, detail="source passage not found")
        return result

    return application


app = create_app()
