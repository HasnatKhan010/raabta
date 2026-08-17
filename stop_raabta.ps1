$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectDirectory "work\raabta-processes.json"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "Raabta is not recorded as running."
    exit 0
}

$processes = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
foreach ($processId in @($processes.api_pid, $processes.web_pid)) {
    if ($processId) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Remove-Item -LiteralPath $pidFile -Force
Write-Host "Raabta has stopped."
