import { FormEvent, useState } from "react";

type Variant = { variant_id: string; variant_type: string; query_text: string; accepted: boolean; semantic_similarity: number; decision_reason: string };
type Evidence = { passage_id: string; title: string; url: string; text: string; similarity: number; retrieval_rank: number };
type Trace = { passage_id: string; rank: number; score: number; route: string; contributing_routes: string[] };
type Comparison = Record<string, { gold_rank: number | null; gold_status: string; passage_ids: string[] }>;
type Result = {
  query: string; supported: boolean; answer: string; query_variants: Variant[];
  evidence: Evidence[]; sources: { title: string; url: string }[]; retrieval_trace: Trace[];
  scores: Record<string, number>; latency_ms: Record<string, number>; abstention_reason: string | null;
  research_comparison: Comparison | null;
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

function App() {
  const [query, setQuery] = useState("pakistan ka capital kya hai");
  const [researchMode, setResearchMode] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!query.trim() || loading) return;
    setLoading(true); setError("");
    try {
      const response = await fetch(`${API}/api/query`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim(), research_mode: researchMode }),
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
          <label className="toggle"><input type="checkbox" checked={researchMode} onChange={(e) => setResearchMode(e.target.checked)} /><span className="switch"/> Research Mode</label>
          <span>Roman Urdu, Urdu, or mixed English</span>
        </div>
      </form>
      {error && <div className="error" role="alert">{error} Is the local API running?</div>}
    </section>

    {result && <section className="results" aria-live="polite">
      <div className="result-head"><div><span className="section-no">01</span><h2>Grounded answer</h2></div><div className={`confidence ${result.supported ? "supported" : "unsupported"}`}>{result.supported ? "Evidence supported" : "Insufficient evidence"}</div></div>
      <article className="answer-card">
        <div className="answer-label">ANSWER · جواب</div>
        <p dir="rtl" lang="ur">{result.answer}</p>
        {result.sources[0] && <a href={result.sources[0].url} target="_blank" rel="noreferrer">{result.sources[0].title}<span>↗</span></a>}
      </article>

      <div className="two-col">
        <section className="panel evidence-panel">
          <div className="panel-title"><span className="section-no">02</span><h2>Exact evidence</h2></div>
          {result.evidence.length ? result.evidence.map((item, index) => <blockquote key={`${item.passage_id}-${index}`} dir="rtl" lang="ur">{item.text}</blockquote>) : <p className="muted">No evidence was strong enough to cite.</p>}
          {result.evidence[0] && <div className="meta"><span>Passage rank {result.evidence[0].retrieval_rank}</span><span>Similarity {result.evidence[0].similarity.toFixed(3)}</span></div>}
        </section>
        <section className="panel">
          <div className="panel-title"><span className="section-no">03</span><h2>QueryBridge</h2></div>
          <div className="variants">{result.query_variants.map((item) => <div className={item.accepted ? "variant" : "variant rejected"} key={item.variant_id}><div><small>{variantNames[item.variant_type] ?? item.variant_type}</small><strong dir={item.variant_type.includes("urdu") || item.variant_type === "retrieval_oriented" ? "rtl" : "ltr"}>{item.query_text}</strong></div><span>{item.accepted ? `${item.semantic_similarity.toFixed(2)} match` : "duplicate"}</span></div>)}</div>
        </section>
      </div>

      <section className="panel trace-panel">
        <div className="panel-title"><span className="section-no">04</span><h2>Retrieval trace</h2><span className="plain-score">Scores rank evidence; they are not probabilities.</span></div>
        <div className="trace-list">{result.retrieval_trace.slice(0, 5).map((item) => <div className="trace-row" key={item.passage_id}><b>{String(item.rank).padStart(2, "0")}</b><code>{item.passage_id}</code><div className="route-tags">{item.contributing_routes.map((route) => <span key={route}>{route.split(":")[0]}</span>)}</div><strong>{item.score.toFixed(4)}</strong></div>)}</div>
      </section>

      {researchMode && result.research_comparison && <section className="research">
        <div className="research-intro"><span className="section-no light">05</span><div><h2>Research Mode</h2><p>Side-by-side retrieval routes for this free-form query. Gold rank is shown only when verified gold evidence is supplied—never inferred.</p></div></div>
        <div className="system-grid">{Object.entries(result.research_comparison).map(([name, data]) => <article key={name}><small>SYSTEM</small><h3>{systemNames[name] ?? name}</h3><p>Gold evidence rank</p><strong>{data.gold_rank ?? "NOT PROVIDED"}</strong><code>Top: {data.passage_ids[0] ?? "NO RESULT"}</code></article>)}</div>
      </section>}

      <footer className="latency"><span>Total processing time</span><strong>{(result.latency_ms.total / 1000).toFixed(2)} s</strong><div><i style={{width: `${Math.min(100, result.latency_ms.retrieval / result.latency_ms.total * 100)}%`}} /></div><small>Retrieval {result.latency_ms.retrieval.toFixed(0)} ms · Evidence selection {result.latency_ms.answer_selection.toFixed(0)} ms</small></footer>
    </section>}
  </main>;
}

export default App;
