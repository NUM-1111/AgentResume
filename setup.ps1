# 一次性：在 job-agent-mvp 下创建 .venv 并安装 requirements.txt
# 用法：在项目根目录执行 .\setup.ps1

$ErrorActionPreference = "Stop"
$projectDir = Join-Path $PSScriptRoot "job-agent-mvp"
$venvPython = Join-Path $projectDir ".venv\Scripts\python.exe"

Write-Host "=== 配置 Python 虚拟环境 ===" -ForegroundColor Cyan
Write-Host "目录: $projectDir" -ForegroundColor Gray

if (-not (Test-Path $projectDir)) {
    Write-Host "未找到 job-agent-mvp 目录。" -ForegroundColor Red
    exit 1
}

Set-Location $projectDir

if (-not (Test-Path $venvPython)) {
    Write-Host "创建虚拟环境 .venv ..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "安装依赖 ..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host "`n完成。在项目根目录运行 .\start.ps1 启动服务。" -ForegroundColor Green
