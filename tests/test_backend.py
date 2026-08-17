from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import create_app


class FakeEngine:
    def query(self, query: str, research_mode: bool = False) -> dict:
        return {
            "query": query,
            "supported": True,
            "answer": "ثبوت۔",
            "query_variants": [],
            "evidence": [],
            "sources": [{"title": "ماخذ", "url": "https://example.test"}],
            "retrieval_trace": [],
            "scores": {"best_evidence_similarity": 0.9},
            "latency_ms": {"retrieval": 1.0, "answer_selection": 2.0, "total": 3.0},
            "abstention_reason": None,
            "research_comparison": {"enabled": True} if research_mode else None,
        }

    def compare(self, query: str, gold_passage_id: str | None = None) -> dict:
        return {"query": query, "gold": gold_passage_id}

    def source(self, passage_id: str) -> dict | None:
        if passage_id != "p1":
            return None
        return {
            "passage_id": "p1",
            "article_id": "a1",
            "title": "ماخذ",
            "url": "https://example.test",
            "passage_text": "ثبوت۔",
            "domain": "general",
        }


class BackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(FakeEngine()))

    def test_health_does_not_require_model_loading(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["engine_loaded"])

    def test_frontend_origin_is_explicitly_allowed(self) -> None:
        response = self.client.options(
            "/api/query",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://127.0.0.1:5173")

    def test_query_contract_and_validation(self) -> None:
        response = self.client.post("/api/query", json={"query": "sawal", "research_mode": True})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "ثبوت۔")
        self.assertIsNotNone(response.json()["research_comparison"])
        self.assertEqual(self.client.post("/api/query", json={"query": "   "}).status_code, 422)

    def test_compare_and_source_endpoints(self) -> None:
        comparison = self.client.post(
            "/api/compare", json={"query": "sawal", "gold_passage_id": "p1"}
        )
        self.assertEqual(comparison.json()["gold"], "p1")
        self.assertEqual(self.client.get("/api/source/p1").status_code, 200)
        self.assertEqual(self.client.get("/api/source/missing").status_code, 404)


if __name__ == "__main__":
    unittest.main()
