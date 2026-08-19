# Verified availability and CPU feasibility

Assessment date: 2026-08-16. Links below point to primary project/model pages.

## Data

- [Wikimedia `20231101.ur`](https://huggingface.co/datasets/wikimedia/wikipedia/tree/3e1f92c331f318af862b87e2319ed5dc26d80f5d/20231101.ur) is present at the pinned dataset revision as one Parquet shard. Its card metadata reports 200,154 examples, 167,627,869 download bytes, and CC BY-SA 3.0/GFDL licenses. The project scan retained 4,000 articles without loading the complete corpus into memory.
- [Roman-Urdu-Parl-split](https://huggingface.co/datasets/Mavkif/Roman-Urdu-Parl-split) declares Apache-2.0 and documents 6,365,808 original pairs. Its training CSV is shown as roughly 1.19 GB, so the pipeline must stream a fixed development sample rather than load the file in memory.

Dataset licenses govern the downloaded content independently of this repository's code license. Attribution and redistribution terms apply whenever processed text is shared.

## Models

- [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small) is an MIT-licensed multilingual encoder. The pinned artifact is about 0.1B parameters with 384-dimensional output and a 512-token input limit. Passage embeddings are cached. For 100,000 passages, float32 vectors require about 146 MiB before metadata/index overhead.
- [`Alibaba-NLP/gte-multilingual-reranker-base`](https://huggingface.co/Alibaba-NLP/gte-multilingual-reranker-base) is Apache-2.0, 306M parameters, and has a model-weight file around 612 MB. CPU execution is possible but must be benchmarked. It is disabled by default and limited to the top 20 candidates.

## Index decision

The first dense baseline uses normalized NumPy arrays and exact dot-product search. This avoids a known portability risk around platform-specific FAISS wheels and is technically sufficient for the planned local subset. FAISS is not ruled out; it will be introduced only if measured passage count/latency justifies it.

## Python compatibility

Python 3.11 is the target. The temporary development environment uses bundled Python 3.12, so code is constrained to the shared 3.11–3.12 surface. Transformer/PyTorch installation is deferred until Phase 2 to avoid a large, unnecessary download during the data phase.
