@echo off
chcp 65001 >nul
echo === 求职智能助手 Agent MVP ===
echo.

set PROJECT_DIR=%~dp0job-agent-mvp

echo [1/2] 启动 FastAPI 后端 (http://localhost:8000)...
start "FastAPI Backend" cmd /k "cd /d %PROJECT_DIR% && py -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 1 /nobreak >nul

echo [2/2] 启动 Streamlit 前端 (http://localhost:8501)...
start "Streamlit Frontend" cmd /k "cd /d %PROJECT_DIR% && py -m streamlit run app.py --server.port 8501"

echo.
echo 两个服务已在独立窗口中启动：
echo   后端 API:  http://localhost:8000/docs
echo   前端页面:  http://localhost:8501
echo.
echo 关闭对应的命令行窗口即可停止服务。
pause