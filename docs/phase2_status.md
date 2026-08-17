# Phase 2 baseline status

Implementation date: 2026-08-16.

## Implemented

- **Direct dense:** normalized exact dot-product retrieval over an aligned NumPy embedding matrix. E5 query/passage prefixes are applied at encoding time.
- **Single transliteration + BM25:** one small deterministic Roman-to-Urdu mapping with unknown tokens preserved, followed by the same transparent BM25 implementation. Its limited vocabulary is intentional so this baseline does not absorb QueryBridge's proposed contribution.
- **Standard hybrid:** raw-query BM25 and direct dense results combined with equal-weight RRF (`k=60`). QueryBridge variants are not included.
- **Metrics:** Recall@K, reciprocal rank/MRR input, and binary-relevance nDCG@K.

## Validation

All baseline components run in fixture tests. The dense unit test uses a deterministic fake encoder, so it validates ranking/index alignment without pretending to validate multilingual model quality. The complete repository currently passes 19 unit tests and `pip check` reports no broken dependencies.

## Real E5 index

- Model: `intfloat/multilingual-e5-small`
- Revision: `d1d99a1efae6779390caba937d92c54b5bc70e51`
- Device: CPU
- Passage matrix: 16,352 × 384, float32
- Build time: 2,546.257 seconds (42.4 minutes)
- Passage SHA-256: `47648cf679facb9a576841542289767f854c1a27aca6cb8e14e3f3eb1a2e5671`
- Embedding SHA-256: `80a612c09c88768c8def7dbe852125f0520afa97f8b88c4b4e6a06d22283bc9a`

The build time demonstrates that full embedding generation is an offline preprocessing operation on this CPU. Cached query-time smoke retrieval across all three routes took 184.258 ms after model, passages, embeddings, and BM25 were loaded; this is not yet a latency benchmark distribution.

## Qualitative smoke observation

For `pakistan ka capital kya hai`, direct dense and single-transliteration BM25 both ranked passage `58191-p0000-b39fd7c03fbb` from *پاکستان کے دارالحکومت* first. The raw-query hybrid was distracted by incidental Latin-token overlap and did not place that passage in its top three.

This observation triggered one correctness fix: BM25 now refuses to rank documents when there is no lexical token overlap, preventing zero-score documents from becoming arbitrary RRF candidates. The remaining hybrid behavior reflects actual nonzero overlap and is retained for later systematic evaluation rather than tuned from one example.

## Integrity boundary

No baseline metric is reported yet. The E5 artifact/index is built, but the annotation queue still contains drafts rather than verified relevance judgments. Running metrics on unverified drafts would create misleading results and is therefore blocked by design.
