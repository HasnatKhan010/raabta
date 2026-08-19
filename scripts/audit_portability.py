"""Audit portable project inputs, locks, checksums, notebooks, and test isolation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "reports/tables/portability_audit.json"
    )
    args = parser.parse_args()
    checks: dict[str, dict] = {}

    def record(name: str, passed: bool, detail) -> None:
        checks[name] = {"passed": bool(passed), "detail": detail}

    record("python_supported", (3, 11) <= sys.version_info[:2] < (3, 13), sys.version.split()[0])
    requirements = []
    for filename in ("requirements.txt", "requirements-dev.txt"):
        requirements.extend(
            line.strip()
            for line in (ROOT / filename).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#") and not line.startswith("-r")
        )
    unpinned = [item for item in requirements if "==" not in item]
    record(
        "python_dependencies_pinned", not unpinned, unpinned or f"{len(requirements)} exact pins"
    )

    lock = ROOT / "frontend/pnpm-lock.yaml"
    record("frontend_lock_present", lock.is_file(), str(lock.relative_to(ROOT)))
    record(
        "frontend_generated_dirs_ignored",
        all(
            item in (ROOT / ".gitignore").read_text(encoding="utf-8")
            for item in ("frontend/node_modules/", "frontend/dist/", ".venv/")
        ),
        "venv, node_modules, and dist are removable",
    )

    phase1 = json.loads(
        (ROOT / "artifacts/metadata/phase1_manifest.json").read_text(encoding="utf-8")
    )
    default_passage = next(
        item for item in phase1["passage_variants"] if item["path"].endswith("150_30.jsonl")
    )
    passage_path = ROOT / default_passage["path"]
    record(
        "passage_checksum",
        passage_path.is_file() and sha256(passage_path) == default_passage["sha256"],
        default_passage["sha256"],
    )
    embedding_manifest = json.loads(
        (ROOT / "artifacts/metadata/e5_small_150_30.json").read_text(encoding="utf-8")
    )
    embedding_path = ROOT / "artifacts/embeddings/e5_small_150_30.npy"
    record(
        "embedding_checksum",
        embedding_path.is_file()
        and sha256(embedding_path) == embedding_manifest["embedding_sha256"],
        embedding_manifest["embedding_sha256"],
    )

    diagnostic_path = ROOT / "data/diagnostic/raabta_diagnostic.csv"
    with diagnostic_path.open(encoding="utf-8-sig", newline="") as handle:
        splits: dict[str, int] = {}
        for row in csv.DictReader(handle):
            splits[row["split"]] = splits.get(row["split"], 0) + 1
    record("diagnostic_split_frozen", splits == {"development": 120, "test": 60}, splits)

    evaluation_reports = sorted((ROOT / "reports/tables").glob("*.json"))
    violations = []
    inspected = 0
    for path in evaluation_reports:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "test_queries_used" in payload:
            inspected += 1
            if payload["test_queries_used"] != 0:
                violations.append(path.name)
    record(
        "locked_test_unused",
        not violations,
        violations or f"{inspected} evaluation reports inspected",
    )

    notebook_paths = sorted((ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb"))
    notebook_issues = []
    for path in notebook_paths:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        if not code_cells or any(cell.get("execution_count") is None for cell in code_cells):
            notebook_issues.append(f"{path.name}: unexecuted")
        if any(
            output.get("output_type") == "error"
            for cell in code_cells
            for output in cell.get("outputs", [])
        ):
            notebook_issues.append(f"{path.name}: error output")
        if not any(cell.get("outputs") for cell in code_cells):
            notebook_issues.append(f"{path.name}: no visible output")
    record(
        "notebooks_executed",
        len(notebook_paths) == 7 and not notebook_issues,
        notebook_issues or [path.name for path in notebook_paths],
    )

    absolute_pattern = re.compile(r"[A-Za-z]:[\\/](?:Users|Documents)[\\/]", re.IGNORECASE)
    scan_extensions = {".py", ".yaml", ".yml", ".toml", ".tsx", ".ts", ".css", ".md", ".ps1"}
    hardcoded = []
    excluded = {".venv", "node_modules", "dist", "work"}
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix.lower() not in scan_extensions
            or excluded.intersection(path.parts)
        ):
            continue
        if absolute_pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
            hardcoded.append(str(path.relative_to(ROOT)))
    record(
        "no_machine_specific_source_paths",
        not hardcoded,
        hardcoded or "all source/config paths are relative",
    )

    required_api = [
        ROOT / "backend/app/main.py",
        ROOT / "backend/app/models.py",
        ROOT / "backend/app/service.py",
    ]
    record(
        "backend_sources_present",
        all(path.is_file() for path in required_api),
        [str(path.relative_to(ROOT)) for path in required_api],
    )
    record(
        "frontend_build_present",
        (ROOT / "frontend/dist/index.html").is_file(),
        "frontend/dist/index.html",
    )

    passed = all(item["passed"] for item in checks.values())
    report = {
        "status": "passed" if passed else "failed",
        "checks": checks,
        "limitations": [
            "External language review is outside the assignment scope.",
            "A fresh PC must recreate .venv and frontend/node_modules; model/data artifacts must be copied or regenerated.",
            "The locked test split remains intentionally unevaluated.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
