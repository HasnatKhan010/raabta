$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDirectory

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Project environment not found. Run setup.ps1 first."
}

& ".\.venv\Scripts\python.exe" -m streamlit run streamlit_app.py
