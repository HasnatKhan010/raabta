from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    research_mode: bool = False
    live_search: bool = False

    @field_validator("query")
    @classmethod
    def non_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be blank")
        return value.strip()


class CompareRequest(QueryRequest):
    gold_passage_id: str | None = None


class QueryResponse(BaseModel):
    query: str
    supported: bool
    answer: str
    query_variants: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    sources: list[dict[str, str]]
    retrieval_trace: list[dict[str, Any]]
    scores: dict[str, float]
    latency_ms: dict[str, float]
    pipeline: dict[str, Any]
    abstention_reason: str | None = None
    research_comparison: dict[str, Any] | None = None


class SourceResponse(BaseModel):
    passage_id: str
    article_id: str
    title: str
    url: str
    passage_text: str
    domain: str


class HealthResponse(BaseModel):
    status: str
    engine_loaded: bool
    artifacts_ready: bool
