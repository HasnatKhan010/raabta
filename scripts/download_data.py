"""Explicit, streamed dataset acquisition for RAABTA Phase 1."""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from raabta.data.io import write_jsonl
from raabta.data.selection import select_deterministic_subset

LOGGER = logging.getLogger("raabta.download")


def _configure_project_cache() -> None:
    """Keep downloaded metadata and data caches inside the removable project folder."""

    project_root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("HF_HOME", str(project_root / "artifacts" / "models" / "huggingface"))


def _use_system_certificate_store() -> None:
    """Use the operating-system trust store when the optional bridge is installed."""

    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()


def _datasets_api():
    _configure_project_cache()
    _use_system_certificate_store()
    try:
        from datasets import load_dataset, load_dataset_builder
    except ImportError as error:
        raise SystemExit(
            "Install requirements.txt inside .venv before downloading data."
        ) from error
    return load_dataset, load_dataset_builder


def _verify_license(path: str, configuration: str | None, revision: str, allowed: set[str]) -> str:
    _, load_dataset_builder = _datasets_api()
    builder = load_dataset_builder(path, configuration, revision=revision)
    declared = (builder.info.license or "").strip().lower()
    if not declared:
        from huggingface_hub import HfApi

        card_data = HfApi().dataset_info(path, revision=revision).card_data
        card_license = getattr(card_data, "license", "") if card_data else ""
        if isinstance(card_license, list):
            declared = ", ".join(str(item) for item in card_license).lower()
        else:
            declared = str(card_license or "").strip().lower()
    if not declared or not any(item in declared for item in allowed):
        raise RuntimeError(
            f"Dataset {path} has unapproved or missing license metadata: {declared!r}"
        )
    LOGGER.info("Verified %s license metadata: %s", path, declared)
    return declared


def download_wikipedia(args: argparse.Namespace) -> int:
    load_dataset, _ = _datasets_api()
    _verify_license(
        args.dataset,
        args.configuration,
        args.revision,
        {"cc-by-sa-3.0", "gfdl", "cc by-sa 3.0"},
    )
    stream: Iterable[Mapping[str, object]] = load_dataset(
        args.dataset,
        args.configuration,
        split="train",
        revision=args.revision,
        streaming=True,
    )
    selected = select_deterministic_subset(
        stream,
        subset_size=args.rows,
        domains=set(args.domains),
        seed=args.seed,
        minimum_tokens=args.minimum_tokens,
    )
    if len(selected) != args.rows:
        raise RuntimeError(f"Only {len(selected)} eligible articles found; expected {args.rows}")
    return write_jsonl(args.output, (article.to_dict() for article in selected))


def download_parallel(args: argparse.Namespace) -> int:
    load_dataset, _ = _datasets_api()
    _verify_license(args.dataset, None, args.revision, {"apache-2.0", "apache 2.0"})
    stream = load_dataset(args.dataset, split="train", revision=args.revision, streaming=True)
    # Hugging Face shard order plus a pinned revision makes this bounded development slice
    # reproducible. It is not described as a statistically representative random sample.
    return write_jsonl(args.output, (dict(record) for record in stream.take(args.rows)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    wikipedia = subparsers.add_parser("wikipedia")
    wikipedia.add_argument("--dataset", default="wikimedia/wikipedia")
    wikipedia.add_argument("--configuration", default="20231101.ur")
    wikipedia.add_argument("--revision", default="3e1f92c331f318af862b87e2319ed5dc26d80f5d")
    wikipedia.add_argument("--rows", type=int, default=4000)
    wikipedia.add_argument("--seed", type=int, default=20250816)
    wikipedia.add_argument("--minimum-tokens", type=int, default=80)
    wikipedia.add_argument(
        "--domains",
        nargs="+",
        default=["history", "geography", "science", "culture", "pakistan", "general"],
    )
    wikipedia.add_argument("--output", type=Path, default=Path("data/raw/wikipedia.jsonl"))
    wikipedia.set_defaults(handler=download_wikipedia)

    parallel = subparsers.add_parser("parallel")
    parallel.add_argument("--dataset", default="Mavkif/Roman-Urdu-Parl-split")
    parallel.add_argument("--revision", default="b9ef670661582b5f17eff68b4e65fbe25f3cb0b9")
    parallel.add_argument("--rows", type=int, default=30000)
    parallel.add_argument("--output", type=Path, default=Path("data/raw/roman_urdu.jsonl"))
    parallel.set_defaults(handler=download_parallel)
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    count = args.handler(args)
    LOGGER.info("Wrote %d records to %s", count, args.output)


if __name__ == "__main__":
    main()
