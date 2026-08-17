"""Build the pinned E5 exact-search passage embedding matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from raabta.data.io import read_jsonl
from raabta.data.models import Passage
from raabta.retrieval.dense import E5Encoder, encode_passages


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passages", type=Path, required=True)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model", default="intfloat/multilingual-e5-small")
    parser.add_argument("--revision", default="d1d99a1efae6779390caba937d92c54b5bc70e51")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--cache", type=Path, default=Path("artifacts/models/huggingface"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    passages = [Passage(**record) for record in read_jsonl(args.passages)]
    encoder = E5Encoder(args.model, args.revision, device="cpu", cache_folder=args.cache)
    started = time.perf_counter()
    embeddings = encode_passages(passages, encoder, batch_size=args.batch_size)
    elapsed = time.perf_counter() - started

    args.embeddings.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.embeddings, embeddings, allow_pickle=False)
    manifest = {
        "model": args.model,
        "revision": args.revision,
        "device": "cpu",
        "passage_file": args.passages.as_posix(),
        "passage_sha256": sha256(args.passages),
        "passages": len(passages),
        "embedding_shape": list(embeddings.shape),
        "embedding_dtype": str(embeddings.dtype),
        "embedding_sha256": sha256(args.embeddings),
        "batch_size": args.batch_size,
        "build_seconds": round(elapsed, 3),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
