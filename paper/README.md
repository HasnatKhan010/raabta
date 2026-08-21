# IEEE assignment paper

This folder contains the Part 11 submission:

- `main.tex`: IEEE conference-format LaTeX source
- `references.bib`: cited papers, datasets, models, and libraries
- `main.pdf`: compiled 6-8 page submission

Compile from the project root with either Tectonic or a TeX distribution that provides `latexmk`:

```powershell
.\.venv\Scripts\python.exe scripts\build_final_paper.py
```

The PDF must be regenerated after every source change. All reported measurements use only the 120-question development split; the locked 60-question test split remains unused.

