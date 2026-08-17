from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SearchResult:
    passage_id: str
    score: float
    rank: int
    route: str
    contributing_routes: tuple[str, ...] = field(default_factory=tuple)
