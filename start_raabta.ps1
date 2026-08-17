$ErrorActionPreference = "Stop"

$projectDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectDirectory ".venv\Scripts\python.exe"
$frontendDirectory = Join-Path $projectDirectory "frontend\dist"
$runtimeDirectory = Join-Path $projectDirectory "work"
$pidFile = Join-Path $runtimeDirectory "raabta-processes.json"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "The local environment is missing. Run setup.ps1 first."
}

if (-not (Test-Path -LiteralPath (Join-Path $frontendDirectory "index.html"))) {
    throw "The built interface is missing from frontend\dist."
}

New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null

$env:HF_HUB_OFFLINE = "1"
$env:PYTHONPATH = "src;."

$api = Start-Process -FilePath $pythonPath `
    -ArgumentList @("-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $projectDirectory -WindowStyle Hidden -PassThru

$web = Start-Process -FilePath $pythonPath `
    -ArgumentList @("-m", "http.server", "5173", "--bind", "127.0.0.1", "--directory", $frontendDirectory) `
    -WorkingDirectory $projectDirectory -WindowStyle Hidden -PassThru

@{
    api_pid = $api.Id
    web_pid = $web.Id
    started_utc = [DateTime]::UtcNow.ToString("o")
} | ConvertTo-Json | Set-Content -LiteralPath $pidFile -Encoding UTF8

$healthy = $false
$maxAttempts = 15
for ($i = 1; $i -le $maxAttempts; $i++) {
    Start-Sleep -Seconds 1
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop
        if ($health.status -eq "ok") {
            $healthy = $true
            break
        }
    }
    catch {
        # Waiting for server to finish initializing
    }
}

if (-not $healthy) {
    Stop-Process -Id $api.Id, $web.Id -Force -ErrorAction SilentlyContinue
    throw "Raabta could not start: API server did not become healthy within $maxAttempts seconds."
}

Start-Process "http://127.0.0.1:5173"
Write-Host "Raabta is ready at http://127.0.0.1:5173"
Write-Host "Run stop_raabta.ps1 when finished."
