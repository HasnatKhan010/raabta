$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDirectory

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $pythonCommand = "py"
        $pythonArguments = @("-3.11")
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonCommand = "python"
        $pythonArguments = @()
    }
    else {
        throw "Python 3 is required. Install it on this computer, then run setup.ps1 again."
    }

    & $pythonCommand @pythonArguments -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
& ".\.venv\Scripts\python.exe" -m pip install --no-deps --no-build-isolation -e .

Write-Host ""
Write-Host "Ready. Activate with: .\.venv\Scripts\Activate.ps1"
