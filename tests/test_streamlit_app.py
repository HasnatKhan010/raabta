import json
from pathlib import Path

import httpx
import pytest

import streamlit_app


def test_normalize_api_url() -> None:
    assert streamlit_app.normalize_api_url("https://example.test/") == "https://example.test"
    with pytest.raises(ValueError, match="must begin"):
        streamlit_app.normalize_api_url("example.test")


def test_artifacts_ready_requires_every_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    files = tuple(tmp_path / name for name in ("passages.jsonl", "embeddings.npy", "lexicon.json"))
    monkeypatch.setattr(streamlit_app, "REQUIRED_ARTIFACTS", files)
    assert not streamlit_app.artifacts_ready()
    for path in files:
        path.write_text("ready", encoding="utf-8")
    assert streamlit_app.artifacts_ready()


def test_api_backend_uses_existing_fastapi_contract() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "artifacts_ready": True})
        assert request.url.path == "/api/query"
        assert json.loads(request.read()) == {
            "query": "pakistan ka capital kya hai",
            "research_mode": True,
            "live_search": False,
        }
        return httpx.Response(200, json={"supported": True, "answer": "evidence"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    backend = streamlit_app.ApiBackend("https://api.example.test/", client=client)
    assert backend.health()["status"] == "ok"
    result = backend.query(
        "pakistan ka capital kya hai",
        research_mode=True,
        live_search=False,
    )
    assert result == {"supported": True, "answer": "evidence"}


def test_display_label_is_user_readable() -> None:
    assert streamlit_app.display_label("no_query_content_overlap") == "no query content overlap"
    assert streamlit_app.display_label(None) == "Not available"
