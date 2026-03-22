# One-time: create .venv under job-agent-mvp, install requirements, bootstrap .env
# Usage: from repo root run .\setup.ps1
# Manual equivalent: cd job-agent-mvp; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt; Copy-Item .env.example .env

$ErrorActionPreference = "Stop"
$projectDir = Join-Path $PSScriptRoot "job-agent-mvp"
$venvPython = Join-Path $projectDir ".venv\Scripts\python.exe"
$envExample = Join-Path $projectDir ".env.example"
$envFile = Join-Path $projectDir ".env"

function Invoke-VenvCreate {
    param([string]$WorkDir)
    Set-Location $WorkDir
    if (Get-Command py -ErrorAction SilentlyContinue) {
        Write-Host "Using: py -3 -m venv .venv" -ForegroundColor Gray
        & py -3 -m venv .venv
        return
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "Using: python -m venv .venv" -ForegroundColor Gray
        & python -m venv .venv
        return
    }
    throw "Neither 'py' nor 'python' found on PATH. Install Python 3.10+ (windows.python.org)."
}

Write-Host "=== Python venv setup ===" -ForegroundColor Cyan
Write-Host "Path: $projectDir" -ForegroundColor Gray

if (-not (Test-Path $projectDir)) {
    Write-Host "job-agent-mvp folder not found." -ForegroundColor Red
    exit 1
}

Set-Location $projectDir

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating .venv ..." -ForegroundColor Yellow
    try {
        Invoke-VenvCreate -WorkDir $projectDir
    } catch {
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path $venvPython)) {
        Write-Host "Failed to create venv at $venvPython" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Checking Python version (need 3.10+) ..." -ForegroundColor Gray
& $venvPython -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python in .venv is older than 3.10. Remove .venv and reinstall Python 3.10+." -ForegroundColor Red
    exit 1
}

Write-Host "Installing dependencies ..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

if ((Test-Path $envExample) -and -not (Test-Path $envFile)) {
    Copy-Item -Path $envExample -Destination $envFile
    Write-Host "Created .env from .env.example (edit OPENAI_API_KEY if needed)." -ForegroundColor Yellow
} elseif (-not (Test-Path $envExample)) {
    Write-Host "Warning: .env.example missing; create .env yourself for LLM keys." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. From repo root run .\start.ps1 or .\start.bat" -ForegroundColor Green
