@echo off
setlocal EnableExtensions
chcp 65001 >nul

set "PROJECT_DIR=%~dp0job-agent-mvp"
set "VENV_PY=%PROJECT_DIR%\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo Virtual env not found: %VENV_PY%
    echo Run setup.bat or setup.ps1 from the repo root first.
    pause
    exit /b 1
)

echo === Job Agent MVP ===
echo.

echo [1/2] FastAPI backend (http://localhost:8000)...
start "FastAPI Backend" /D "%PROJECT_DIR%" cmd /k ""%VENV_PY%" -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 1 /nobreak >nul

echo [2/2] Streamlit frontend (http://localhost:8501)...
start "Streamlit Frontend" /D "%PROJECT_DIR%" cmd /k ""%VENV_PY%" -m streamlit run app.py --server.port 8501"

echo.
echo Services started in new windows:
echo   API docs: http://localhost:8000/docs
echo   Streamlit: http://localhost:8501
echo.
echo Close those windows to stop.
pause
