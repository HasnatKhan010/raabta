# Assignment paper

`main.tex` is the generated source and `main.pdf` is the compiled assignment report. Rebuild both from the measured JSON reports with:

```powershell
.\.venv\Scripts\python.exe scripts\build_final_paper.py
```

The report uses development-set measurements only; the locked test split remains unused.

