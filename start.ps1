# 启动脚本：同时启动 FastAPI 后端 + Streamlit 前端
# 用法：在项目根目录右键 "用 PowerShell 运行"，或在终端执行 .\start.ps1

$projectDir = "$PSScriptRoot\job-agent-mvp"

Write-Host "=== 求职智能助手 Agent MVP ===" -ForegroundColor Cyan
Write-Host "启动目录: $projectDir" -ForegroundColor Gray

# 启动 FastAPI 后端（新窗口）
Write-Host "`n[1/2] 启动 FastAPI 后端 (http://localhost:8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectDir'; uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# 稍等一秒，让后端先起来
Start-Sleep -Seconds 1

# 启动 Streamlit 前端（新窗口）
Write-Host "[2/2] 启动 Streamlit 前端 (http://localhost:8501)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectDir'; streamlit run app.py --server.port 8501"

Write-Host "`n✅ 两个服务已在独立窗口中启动" -ForegroundColor Green
Write-Host "   后端 API:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   前端页面:  http://localhost:8501" -ForegroundColor Cyan
Write-Host "`n关闭对应的 PowerShell 窗口即可停止服务。" -ForegroundColor Gray
