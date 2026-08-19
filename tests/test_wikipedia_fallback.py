from __future__ import annotations

import json

from raabta.retrieval.wikipedia import UrduWikipediaClient


class FakeResponse:
    def read(self) -> bytes:
        return json.dumps(
            {
                "query": {
                    "pages": [
                        {
                            "pageid": 123,
                            "index": 1,
                            "title": "محمد علی جناح",
                            "fullurl": "https://ur.wikipedia.org/wiki/example",
                            "extract": "محمد علی جناح 25 دسمبر 1876ء کو پیدا ہوئے۔ وہ پاکستان کے بانی تھے۔",
                        }
                    ]
                }
            },
            ensure_ascii=False,
        ).encode("utf-8")


def test_live_wikipedia_results_are_traceable_passages() -> None:
    calls = []

    def opener(request, timeout):
        calls.append((request.full_url, timeout))
        return FakeResponse()

    client = UrduWikipediaClient(opener=opener)
    result = client.search("قائد اعظم کب پیدا ہوئے")

    assert result.error is None
    assert len(result.passages) == 1
    assert result.passages[0].title == "محمد علی جناح"
    assert result.passages[0].domain == "live_wikipedia"
    assert "generator=search" in calls[0][0]
    assert calls[0][1] == 8.0
