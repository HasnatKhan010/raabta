# Notebooks

Seven phase-specific notebooks execute top-to-bottom from frozen local artifacts. They use fixed seeds, contain visible outputs, avoid hidden state, and keep the locked test split untouched. Run `scripts/execute_notebooks.py` from the project root to re-execute them without requiring Jupyter; they also remain valid standard `.ipynb` files for JupyterLab.

The notebooks summarize existing measured artifacts instead of repeating multi-hour CPU model runs. The scripts that generate those measurements remain the source of truth, and important summaries are stored under `reports/`.
