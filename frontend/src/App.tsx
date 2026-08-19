import { FormEvent, useState } from "react";

type Variant = { variant_id: string; variant_type: string; query_text: string; accepted: boolean; semantic_similarity: number; decision_reason: string; transliteration_coverage?: number };
type Evidence = { passage_id: string; title: string; url: string; text: string; similarity: number; retrieval_rank: number };
type Trace = { passage_id: string; rank: number; score: number; route: string; contributing_routes: string[]; title?: string; url?: string; snippet?: string; domain?: string; score_type?: string };
type Comparison = Record<string, { gold_rank: number | null; gold_status: string; passage_ids: string[] }>;
type PipelineStage = { id: string; label: string; status: "passed" | "failed" | "no_match" | "skipped"; detail: string };
type ValidationCheck = { id: string; label: string; status: "passed" | "failed"; value?: number | string; threshold?: number | string; detail?: string | null };
type Pipeline = { mode: string; decision: string; confidence: string; reranker_query: string | null; local_candidate_count: number; live_candidate_count: number; live_search_requested: boolean; live_search_error?: string | null; top_relevance_score?: number; content_overlap?: number; title_match_score?: number; query_intent?: string; reasons: string[]; corpus_notice: string; accepted_variant_count?: number; route_candidate_counts?: Record<string, number>; validation_checks?: ValidationCheck[]; stages?: PipelineStage[] };
type Result = {
  query: string; supported: boolean; answer: string; query_variants: Variant[];
  evidence: Evidence[]; sources: { title: string; url: string }[]; retrieval_trace: Trace[];
  scores: Record<string, number>; latency_ms: Record<string, number>; abstention_reason: string | null;
  pipeline: Pipeline; research_comparison: Comparison | null;
};

const API = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
const variantNames: Record<string, string> = {
  original: "Original query", normalized_roman: "Normalized Roman",
  urdu_script: "Urdu query", retrieval_oriented: "Retrieval variant",
};
const systemNames: Record<string, string> = {
  direct_dense: "Direct dense", single_transliteration_bm25: "Single transliteration",
  standard_hybrid: "Standard hybrid", raabta_no_reranker: "Raabta",
};
const routeNames: Record<string, string> = {
  roman_title: "Romanized Urdu title",
  bm25: "Exact-word BM25",
  dense: "Multilingual semantic",
  reranker: "Cross-encoder reranker",
};
const prettyRoute = (route: string) => routeNames[route.split(":")[0]] ?? route.replaceAll("_", " ");
const showValue = (value: number | string | undefined) => typeof value === "number" ? value.toFixed(3) : value ?? "—";

function App() {
  const [query, setQuery] = useState("pakistan ka capital kya hai");
  const [researchMode, setResearchMode] = useState(false);
  const [liveSearch, setLiveSearch] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const response = await fetch(`${API}/api/query`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), research_mode: researchMode, live_search: liveSearch }),
      });
      if (!response.ok) throw new Error(response.status === 422 ? "Please enter a valid question." : "Raabta could not complete this query.");
      setResult(await response.json());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The local service is unavailable.");
    } finally { setLoading(false); }
  }

  return <main>
    <header className="nav">
      <a className="wordmark" href="#top" aria-label="Raabta home"><span>رابطہ</span> RAABTA</a>
      <div className="status"><i /> Local evidence system</div>
    </header>

    <section className="hero" id="top">
      <div className="eyebrow"><span /> ROMAN URDU → اردو EVIDENCE</div>
      <h1>Ask naturally.<br/><em>See the evidence.</em></h1>
      <p className="intro">Raabta bridges everyday Roman-Urdu questions to precise, traceable knowledge in Urdu script.</p>
      <form onSubmit={submit} className="query-box">
        <label htmlFor="query">Your question</label>
        <div className="input-row">
          <input id="query" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="quaid e azam kb paida hue?" maxLength={500} />
          <button type="submit" disabled={loading}>{loading ? "Finding evidence…" : "Ask Raabta"}<span>→</span></button>
        </div>
        <div className="form-footer">
          <div className="search-options">
            <label className="toggle"><input type="checkbox" checked={researchMode} onChange={(e) => setResearchMode(e.target.checked)} /><span className="switch"/> Research Mode</label>
            <label className="toggle"><input type="checkbox" checked={liveSearch} onChange={(e) => setLiveSearch(e.target.checked)} /><span className="switch"/> Live Urdu Wikipedia fallback</label>
          </div>
          <span>Roman Urdu, Urdu, or mixed English</span>
        </div>
      </form>
      {error && <div className="error" role="alert">{error} Is the local API running?</div>}
      {loading && <div className="working" role="status">
        <div><strong>Raabta is checking the evidence</strong><span>CPU reranking may take 15–25 seconds.</span></div>
        <ol><li>Normalize</li><li>Convert script</li><li>Match Urdu titles</li><li>Hybrid retrieve</li><li>Rerank</li><li>Validate or abstain</li></ol>
        {liveSearch && <p>Your query may be sent to Urdu Wikipedia only if the local corpus fails.</p>}
      </div>}
    </section>

    {result && <section className="results" aria-live="polite">
      <div className="result-head"><div><span className="section-no">01</span><h2>Grounded answer</h2></div><div className={`confidence ${result.supported ? "supported" : "unsupported"}`}>{result.supported ? `${result.pipeline.confidence} confidence · evidence supported` : "Rejected · insufficient evidence"}</div></div>
      <article className={`answer-card ${result.supported ? "" : "answer-rejected"}`}>
        <div className="answer-label">ANSWER · جواب</div>
        <p dir="rtl" lang="ur">{result.answer}</p>
        {result.sources[0] && <a href={result.sources[0].url} target="_blank" rel="noreferrer">{result.sources[0].title}<span>↗</span></a>}
      </article>

      <section className="pipeline-panel">
        <div className="pipeline-heading"><div><span className="section-no">02</span><h2>What actually happened</h2></div><span className={`mode-badge mode-${result.pipeline.mode}`}>{result.pipeline.mode.replaceAll("_", " ")}</span></div>
        <div className="pipeline-grid">
          <div><small>QUERY USED FOR RERANKING</small><strong dir="auto">{result.pipeline.reranker_query ?? "Verified fact card"}</strong></div>
          <div><small>TOP RELEVANCE</small><strong>{(result.pipeline.top_relevance_score ?? result.scores.top_reranker_score ?? 0).toFixed(3)}</strong></div>
          <div><small>QUERY ↔ SOURCE ALIGNMENT</small><strong>{Math.round(Math.max(result.pipeline.content_overlap ?? 0, result.pipeline.title_match_score ?? 0) * 100)}%</strong></div>
          <div><small>CANDIDATES CHECKED</small><strong>{result.pipeline.local_candidate_count}{result.pipeline.live_candidate_count ? ` + ${result.pipeline.live_candidate_count} live` : ""}</strong></div>
        </div>
        {!!result.pipeline.stages?.length && <div className="pipeline-flow" aria-label="Completed search stages">
          {result.pipeline.stages.map((stage, index) => <article className={`flow-step flow-${stage.status}`} key={stage.id}>
            <div className="flow-marker"><b>{String(index + 1).padStart(2, "0")}</b><i /></div>
            <div><div className="flow-title"><strong>{stage.label}</strong><span>{stage.status.replaceAll("_", " ")}</span></div><p>{stage.detail}</p></div>
          </article>)}
        </div>}
        {!!result.pipeline.validation_checks?.length && <section className="gate-panel">
          <div className="gate-heading"><strong>Evidence gates</strong><span>Every required gate must pass before an answer is shown.</span></div>
          <div className="gate-grid">{result.pipeline.validation_checks.map((check) => <article className={`gate gate-${check.status}`} key={check.id}>
            <div><i /><strong>{check.label}</strong><span>{check.status}</span></div>
            {(check.value !== undefined || check.threshold !== undefined) && <p>Observed <b>{showValue(check.value)}</b>{check.threshold !== undefined && <> · Required <b>{showValue(check.threshold)}</b></>}</p>}
            {check.detail && <small>{check.detail}</small>}
          </article>)}</div>
        </section>}
        {!!Object.keys(result.pipeline.route_candidate_counts ?? {}).length && <details className="route-details">
          <summary>Show every retrieval route and candidate count</summary>
          <div>{Object.entries(result.pipeline.route_candidate_counts ?? {}).map(([route, count]) => <span key={route}><b>{prettyRoute(route)}</b><small>{route}</small><strong>{count}</strong></span>)}</div>
        </details>}
        <ul className="decision-list">{result.pipeline.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
        <p className="corpus-notice">{result.pipeline.corpus_notice}</p>
        {!result.supported && !result.pipeline.live_search_requested && <p className="next-action">Need broader coverage? Enable <b>Live Urdu Wikipedia fallback</b> and retry. The query will leave this PC only when that option is enabled.</p>}
      </section>

      <div className="two-col">
        <section className="panel evidence-panel">
          <div className="panel-title"><span className="section-no">03</span><h2>Exact evidence</h2></div>
          {result.evidence.length ? result.evidence.map((item, index) => <blockquote key={`${item.passage_id}-${index}`} dir="rtl" lang="ur">{item.text}</blockquote>) : <p className="muted">No evidence was strong enough to cite.</p>}
          {result.evidence[0] && <div className="meta"><span>Passage rank {result.evidence[0].retrieval_rank}</span><span>Similarity {result.evidence[0].similarity.toFixed(3)}</span></div>}
        </section>
        <section className="panel">
          <div className="panel-title"><span className="section-no">04</span><h2>QueryBridge</h2></div>
          <div className="variants">{result.query_variants.map((item) => <div className={item.accepted ? "variant" : "variant rejected"} key={item.variant_id}><div><small>{variantNames[item.variant_type] ?? item.variant_type}</small><strong dir={item.variant_type.includes("urdu") || item.variant_type === "retrieval_oriented" ? "rtl" : "ltr"}>{item.query_text}</strong></div><span>{item.accepted ? `${item.semantic_similarity.toFixed(2)} semantic · ${Math.round((item.transliteration_coverage ?? 1) * 100)}% converted` : item.decision_reason.replaceAll("_", " ")}</span></div>)}</div>
        </section>
      </div>

      <section className="panel trace-panel">
        <div className="panel-title"><span className="section-no">05</span><h2>Candidate evidence</h2><span className="plain-score">Low-scoring candidates are shown for transparency, not as answers.</span></div>
        <div className="trace-list">{result.retrieval_trace.slice(0, 5).map((item) => <div className="trace-row" key={item.passage_id}><b>{String(item.rank).padStart(2, "0")}</b><div className="trace-copy"><strong>{item.title ?? item.passage_id}</strong><p dir="auto">{item.snippet ?? item.passage_id}</p></div><div className="route-tags">{item.contributing_routes.map((route) => <span key={route}>{prettyRoute(route)}</span>)}</div><div className="trace-score"><small>reranker relevance</small><strong>{item.score.toFixed(4)}</strong></div></div>)}</div>
      </section>

      {researchMode && result.research_comparison && <section className="research">
        <div className="research-intro"><span className="section-no light">06</span><div><h2>Research Mode</h2><p>Side-by-side retrieval routes for this free-form query. Gold rank is shown only when verified gold evidence is supplied—never inferred.</p></div></div>
        <div className="system-grid">{Object.entries(result.research_comparison).map(([name, data]) => <article key={name}><small>SYSTEM</small><h3>{systemNames[name] ?? name}</h3><p>Gold evidence rank</p><strong>{data.gold_rank ?? "NOT PROVIDED"}</strong><code>Top: {data.passage_ids[0] ?? "NO RESULT"}</code></article>)}</div>
      </section>}

      <footer className="latency"><span>Total processing time</span><strong>{(result.latency_ms.total / 1000).toFixed(2)} s</strong><div><i style={{width: `${Math.min(100, result.latency_ms.retrieval / result.latency_ms.total * 100)}%`}} /></div><small>Hybrid retrieval {(result.latency_ms.hybrid_retrieval ?? 0).toFixed(0)} ms · Reranking {(result.latency_ms.reranking ?? 0).toFixed(0)} ms · Live fallback {(result.latency_ms.live_search ?? 0).toFixed(0)} ms · Evidence validation {result.latency_ms.answer_selection.toFixed(0)} ms</small></footer>
    </section>}
  </main>;
}

export default App;
