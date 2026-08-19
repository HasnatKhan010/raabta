"""Optional live Urdu-Wikipedia fallback for gaps in the bounded local corpus."""

from __future__ import annotations

import html
import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from raabta.data.models import Article, Passage
from raabta.preprocessing.chunking import chunk_article

_ENDPOINT = "https://ur.wikipedia.org/w/api.php"


@dataclass(frozen=True, slots=True)
class WikipediaSearchResult:
    passages: tuple[Passage, ...]
    error: str | None = None


class UrduWikipediaClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 8.0,
        opener: Callable[..., object] = urllib.request.urlopen,
    ) -> None:
        try:
            import truststore

            truststore.inject_into_ssl()
        except ImportError:
            pass
        self.timeout_seconds = timeout_seconds
        self.opener = opener
        self._cache: dict[str, WikipediaSearchResult] = {}

    def search(self, query: str, *, page_limit: int = 5) -> WikipediaSearchResult:
        normalized = " ".join(query.split())
        if not normalized:
            return WikipediaSearchResult((), "empty_live_query")
        if normalized in self._cache:
            return self._cache[normalized]
        parameters = urllib.parse.urlencode(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": normalized,
                "gsrlimit": page_limit,
                "prop": "extracts|info",
                "exintro": "1",
                "explaintext": "1",
                "inprop": "url",
                "redirects": "1",
                "format": "json",
                "formatversion": "2",
            }
        )
        request = urllib.request.Request(
            f"{_ENDPOINT}?{parameters}",
            headers={"User-Agent": "Raabta/0.2 (local educational retrieval prototype)"},
        )
        try:
            response = self.opener(request, timeout=self.timeout_seconds)
            payload = json.loads(response.read().decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, urllib.error.URLError) as error:
            result = WikipediaSearchResult((), f"live_wikipedia_unavailable:{type(error).__name__}")
            self._cache[normalized] = result
            return result

        passages: list[Passage] = []
        pages = payload.get("query", {}).get("pages", [])
        for page in sorted(pages, key=lambda item: item.get("index", 9999)):
            extract = html.unescape(page.get("extract", "")).strip()
            if len(extract.split()) < 8:
                continue
            page_id = str(page.get("pageid", "unknown"))
            article = Article(
                article_id=f"live-wikipedia-{page_id}",
                title=page.get("title", "Urdu Wikipedia"),
                url=page.get("fullurl", "https://ur.wikipedia.org/"),
                raw_text=extract,
                clean_text=extract,
                domain="live_wikipedia",
            )
            passages.extend(chunk_article(article, chunk_size=160, overlap=20))
        result = WikipediaSearchResult(tuple(passages))
        self._cache[normalized] = result
        return result
