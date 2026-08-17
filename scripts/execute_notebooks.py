"""Execute the project's simple standard-library notebooks top to bottom."""

from __future__ import annotations

import contextlib
import io
import json
import os
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    original = Path.cwd()
    os.chdir(ROOT)
    try:
        for path in sorted((ROOT / "notebooks").glob("[0-9][0-9]_*.ipynb")):
            notebook = json.loads(path.read_text(encoding="utf-8"))
            namespace = {"__name__": "__notebook__"}
            execution_count = 0
            for cell in notebook["cells"]:
                if cell["cell_type"] != "code":
                    continue
                execution_count += 1
                stream = io.StringIO()
                cell["outputs"] = []
                try:
                    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                        exec(compile("".join(cell["source"]), str(path), "exec"), namespace)
                    text = stream.getvalue()
                    if text:
                        cell["outputs"].append(
                            {"name": "stdout", "output_type": "stream", "text": [text]}
                        )
                except Exception as error:
                    cell["outputs"].append(
                        {
                            "ename": type(error).__name__,
                            "evalue": str(error),
                            "output_type": "error",
                            "traceback": traceback.format_exc().splitlines(),
                        }
                    )
                    path.write_text(
                        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
                    )
                    raise
                cell["execution_count"] = execution_count
            path.write_text(
                json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
            )
            print(f"executed {path.name}: {execution_count} code cells")
    finally:
        os.chdir(original)


if __name__ == "__main__":
    main()
