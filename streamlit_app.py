"""Quick Streamlit interface for the existing Raabta retrieval service."""

from __future__ import annotations

import html
import os
from pathlib import Path
from threading import Lock
from typing import Any, Protocol

import httpx
import streamlit as st

from backend.app.service import RaabtaEngine

ROOT = Path(__file__).resolve().parent
REQUIRED_ARTIFACTS = (
    ROOT / "data/processed/passages_150_30.jsonl",
    ROOT / "artifacts/embeddings/e5_small_150_30.npy",
    ROOT / "artifacts/metadata/transliteration_lexicon.json",
)
EXAMPLES = (
    "pakistan ka capital kya hai",
    "quaid e azam kb paida hue",
    "allama iqbal kon thay",
)


class QueryBackend(Protocol):
    label: str

    def query(self, query: str, *, research_mode: bool, live_search: bool) -> dict[str, Any]: ...

    def health(self) -> dict[str, Any]: ...


class LocalBackend:
    """Thread-safe adapter around the same engine used by FastAPI."""

    label = "Full local Raabta engine"

    def __init__(self, root: Path) -> None:
        self.engine = RaabtaEngine(root)
        self._lock = Lock()

    def query(self, query: str, *, research_mode: bool, live_search: bool) -> dict[str, Any]:
        with self._lock:
            return self.engine.query(query, research_mode, live_search)

    def health(self) -> dict[str, Any]:
        return {"status": "ok", "engine_loaded": True, "artifacts_ready": True}


class ApiBackend:
    """Small client for a separately hosted Raabta FastAPI service."""

    def __init__(self, api_url: str, *, client: httpx.Client | None = None) -> None:
        self.api_url = normalize_api_url(api_url)
        self.label = f"FastAPI backend · {self.api_url}"
        self.client = client or httpx.Client(timeout=httpx.Timeout(180.0, connect=15.0))

    def query(self, query: str, *, research_mode: bool, live_search: bool) -> dict[str, Any]:
        response = self.client.post(
            f"{self.api_url}/api/query",
            json={
                "query": query,
                "research_mode": research_mode,
                "live_search": live_search,
            },
        )
        response.raise_for_status()
        return response.json()

    def health(self) -> dict[str, Any]:
        response = self.client.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()


def normalize_api_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value.startswith(("http://", "https://")):
        raise ValueError("RAABTA_API_URL must begin with http:// or https://")
    return value


def artifacts_ready() -> bool:
    return all(path.is_file() for path in REQUIRED_ARTIFACTS)


def configured_api_url() -> str:
    environment_value = os.getenv("RAABTA_API_URL", "").strip()
    if environment_value:
        return environment_value
    try:
        return str(st.secrets.get("RAABTA_API_URL", "")).strip()
    except (FileNotFoundError, KeyError):
        return ""


@st.cache_resource(show_spinner="Loading the local corpus and multilingual models…")
def load_local_backend(root: str) -> LocalBackend:
    return LocalBackend(Path(root))


@st.cache_resource(show_spinner=False)
def load_api_backend(api_url: str) -> ApiBackend:
    return ApiBackend(api_url)


def display_label(value: str | None) -> str:
    if not value:
        return "Not available"
    return value.replace("_", " ").replace(":", ": ")


def status_icon(status: str) -> str:
    return {"passed": "✓", "failed": "✕", "no_match": "–"}.get(status, "•")


def render_answer(result: dict[str, Any]) -> None:
    supported = bool(result.get("supported"))
    if supported:
        st.success("Reliable evidence found")
        answer = html.escape(str(result.get("answer", "")))
        st.markdown(f'<div class="answer" dir="rtl">{answer}</div>', unsafe_allow_html=True)
    else:
        st.warning("Raabta abstained instead of showing an unsupported result")
        st.write(display_label(result.get("abstention_reason")))

    sources = result.get("sources", [])
    if sources:
        st.markdown("#### Source")
        for source in sources:
            st.markdown(f'- [{source.get("title", "Source")}]({source.get("url", "")})')

    pipeline = result.get("pipeline", {})
    scores = result.get("scores", {})
    latency = result.get("latency_ms", {})
    columns = st.columns(4)
    columns[0].metric("Confidence", str(pipeline.get("confidence", "unknown")).title())
    columns[1].metric("Relevance", f'{scores.get("top_reranker_score", 0.0):.3f}')
    columns[2].metric("Evidence", f'{scores.get("best_evidence_similarity", 0.0):.3f}')
    columns[3].metric("Total time", f'{latency.get("total", 0.0):,.0f} ms')


def render_process(result: dict[str, Any]) -> None:
    pipeline = result.get("pipeline", {})
    st.subheader("What happened")
    for stage in pipeline.get("stages", []):
        status = str(stage.get("status", "unknown"))
        st.markdown(
            f'**{status_icon(status)} {stage.get("label", "Stage")}** — '
            f'{stage.get("detail", "No detail recorded.")}'
        )

    with st.expander("Validation gates", expanded=True):
        checks = pipeline.get("validation_checks", [])
        if not checks:
            st.caption("No validation gates were needed for this exact fact-card match.")
        for check in checks:
            status = str(check.get("status", "unknown"))
            value = check.get("value")
            threshold = check.get("threshold")
            measurement = ""
            if value is not None or threshold is not None:
                measurement = f" · value {value} · threshold {threshold}"
            st.markdown(
                f'**{status_icon(status)} {check.get("label", "Check")}**{measurement}  \n'
                f'{check.get("detail", "")}'
            )


def render_details(result: dict[str, Any]) -> None:
    variants = result.get("query_variants", [])
    with st.expander(f"Query views ({len(variants)})"):
        if variants:
            st.dataframe(
                [
                    {
                        "type": item.get("variant_type"),
                        "query": item.get("query_text"),
                        "accepted": item.get("accepted"),
                        "similarity": item.get("semantic_similarity"),
                        "coverage": item.get("transliteration_coverage"),
                        "reason": display_label(item.get("decision_reason")),
                    }
                    for item in variants
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.caption("The answer used an exact verified fact card, so query conversion was skipped.")

    pipeline = result.get("pipeline", {})
    route_counts = pipeline.get("route_candidate_counts", {})
    with st.expander(f"Retrieval routes ({len(route_counts)})"):
        if route_counts:
            st.dataframe(
                [{"route": route, "candidates": count} for route, count in route_counts.items()],
                use_container_width=True,
                hide_index=True,
            )
        trace = result.get("retrieval_trace", [])
        if trace:
            st.markdown("**Top reranked candidates**")
            st.dataframe(
                [
                    {
                        "rank": item.get("rank"),
                        "title": item.get("title"),
                        "score": round(float(item.get("score", 0.0)), 4),
                        "domain": item.get("domain"),
                        "routes": ", ".join(item.get("contributing_routes", [])),
                    }
                    for item in trace[:10]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with st.expander("Timing details"):
        st.dataframe(
            [
                {"component": name.replace("_", " "), "milliseconds": value}
                for name, value in result.get("latency_ms", {}).items()
            ],
            use_container_width=True,
            hide_index=True,
        )

    comparison = result.get("research_comparison")
    if comparison:
        with st.expander("Research-mode comparison"):
            st.caption(
                "Gold rank is NOT PROVIDED for normal user questions because no verified gold passage was supplied."
            )
            st.dataframe(
                [
                    {
                        "system": name,
                        "gold status": values.get("gold_status"),
                        "gold rank": values.get("gold_rank") or "—",
                        "returned passages": len(values.get("passage_ids", [])),
                    }
                    for name, values in comparison.items()
                ],
                use_container_width=True,
                hide_index=True,
            )


def resolve_backend() -> QueryBackend | None:
    api_url = configured_api_url()
    if api_url:
        try:
            return load_api_backend(normalize_api_url(api_url))
        except ValueError as error:
            st.error(str(error))
            return None
    if artifacts_ready():
        try:
            return load_local_backend(str(ROOT))
        except Exception as error:  # noqa: BLE001 - initialization failures must be user-visible
            st.error("The local Raabta engine could not be loaded.")
            st.exception(error)
            return None
    return None


def main() -> None:
    st.set_page_config(page_title="Raabta · Evidence Search", page_icon="ر", layout="wide")
    st.markdown(
        """
        <style>
        .stApp { background: #f6f5ef; }
        .block-container { max-width: 1120px; padding-top: 2rem; }
        .hero { padding: 1.4rem 1.5rem; border-radius: 18px; background: #163f3d; color: white; margin-bottom: 1rem; }
        .hero h1 { margin: 0; color: white; }
        .hero p { margin: .45rem 0 0; color: #d9ebe8; }
        .answer { font-size: 1.45rem; line-height: 2.1; padding: 1.2rem 1.4rem; border-radius: 14px; background: white; border: 1px solid #d8dfdc; margin: .7rem 0 1rem; }
        </style>
        <div class="hero">
          <h1>Raabta</h1>
          <p>Ask in Roman Urdu. See the exact Urdu evidence, source, validation decisions, and retrieval trace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Search options")
        research_mode = st.toggle("Research mode", help="Show baseline route comparisons.")
        live_search = st.toggle(
            "Live Urdu Wikipedia fallback",
            help="Used only after local evidence is rejected. The query may leave this computer.",
        )
        if live_search:
            st.warning("Privacy: a failed local query may be sent to Urdu Wikipedia.")

    backend = resolve_backend()
    if backend is None:
        st.error("No usable Raabta backend was found.")
        st.markdown(
            "Run this app from the prepared project folder containing `data/` and `artifacts/`, "
            "or configure `RAABTA_API_URL` in the environment/Streamlit secrets to point at the "
            "existing FastAPI service. No fallback demo answer will be fabricated."
        )
        st.stop()

    with st.sidebar:
        st.divider()
        st.caption("Backend")
        st.write(backend.label)
        try:
            health = backend.health()
            if health.get("status") == "ok" and health.get("artifacts_ready", True):
                st.success("Ready")
            else:
                st.warning("Backend responded, but artifacts are not ready.")
        except (httpx.HTTPError, OSError) as error:
            st.error(f"Backend health check failed: {error}")

    example = st.selectbox("Example question", ("Write my own question", *EXAMPLES))
    initial_query = "" if example == "Write my own question" else example
    with st.form("raabta_query"):
        query = st.text_input(
            "Your Roman-Urdu question",
            value=initial_query,
            placeholder="quaid e azam kb paida hue?",
            max_chars=500,
        )
        submitted = st.form_submit_button("Search evidence", type="primary", use_container_width=True)

    if submitted:
        clean_query = query.strip()
        if not clean_query:
            st.error("Please enter a question.")
        else:
            try:
                with st.spinner("Searching, reranking, and validating evidence…"):
                    st.session_state["raabta_result"] = backend.query(
                        clean_query,
                        research_mode=research_mode,
                        live_search=live_search,
                    )
            except httpx.HTTPStatusError as error:
                st.error(f"The FastAPI backend rejected the query: HTTP {error.response.status_code}")
            except (httpx.HTTPError, OSError, RuntimeError, ValueError) as error:
                st.error(f"Raabta could not complete the query: {error}")

    result = st.session_state.get("raabta_result")
    if result:
        render_answer(result)
        render_process(result)
        render_details(result)

    st.divider()
    st.caption(
        "Raabta returns extractive evidence or abstains. Development Recall@10 is a retrieval metric, not unrestricted answer accuracy."
    )


if __name__ == "__main__":
    main()
