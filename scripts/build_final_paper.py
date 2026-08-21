"""Compile the IEEE LaTeX assignment paper to paper/main.pdf."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"


def main() -> None:
    tectonic = shutil.which("tectonic")
    latexmk = shutil.which("latexmk")
    if tectonic:
        command = [tectonic, "main.tex", "--keep-logs"]
    elif latexmk:
        command = [latexmk, "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"]
    else:
        raise RuntimeError(
            "A LaTeX engine is required. Install Tectonic or a TeX distribution with latexmk."
        )
    subprocess.run(command, cwd=PAPER, check=True)
    output = PAPER / "main.pdf"
    if not output.is_file():
        raise RuntimeError("LaTeX completed without producing paper/main.pdf")
    print(output)


if __name__ == "__main__":
    main()
