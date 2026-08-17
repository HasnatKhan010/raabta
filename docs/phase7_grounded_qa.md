# Phase 7 — evidence-grounded extractive QA

Phase 7 adds a deterministic answer layer over retrieved passages. It does not use a generative LLM.

## Behavior

1. Split the top five retrieved passages into source-preserving Urdu/Latin sentences.
2. Compare sentences against accepted, drift-filtered QueryBridge representations using the pinned E5 encoder.
3. Select the strongest sentence and, when requested, its strongest adjacent sentence from the same passage for coherent context.
4. Return those exact sentence strings as the answer, together with passage/article IDs, title, URL, sentence offsets, similarity, and retrieval rank.
5. Abstain with `دستیاب شواہد سے قابل اعتماد جواب نہیں ملا۔` when no evidence exists or the best similarity is below the configured threshold. An abstention contains no evidence or source citation.

The default evidence threshold is 0.70. This is a conservative engineering default, not a calibrated final threshold; calibration must use reviewed development annotations only.

## Real-corpus smoke test

Query: `pakistan ka capital kya hai`

The system retrieved `پاکستان کے دارالحکومت` at rank 1 and returned exact evidence stating that Islamabad has been Pakistan's national/federal capital since 1960. The response includes the Urdu Wikipedia URL and complete query/retrieval trace. On the local CPU run, retrieval plus evidence selection took approximately 1.7 seconds, excluding cold model loading.

## Run locally

```powershell
$env:HF_HUB_OFFLINE = "1"
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe scripts\query_grounded.py "pakistan ka capital kya hai"
```

The machine-readable smoke artifact is `reports/tables/grounded_qa_smoke.json`.
