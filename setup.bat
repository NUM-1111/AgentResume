@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0job-agent-mvp" || exit /b 1

set "VENV_PY=%CD%\.venv\Scripts\python.exe"


echo === Python venv setup (job-agent-mvp) ===
echo Path: %CD%
echo.

if not exist "%VENV_PY%" (
    echo Creating .venv ...
    py -3 -m venv .venv 2>nul
    if errorlevel 1 python -m venv .venv
    if not exist "%VENV_PY%" (
        echo ERROR: Could not create venv. Install Python 3.10+ and ensure py or python is on PATH.
        exit /b 1
    )
)

echo Installing dependencies ...
"%VENV_PY%" -m pip install --upgrade pip
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if exist ".env.example" if not exist ".env" (
    copy /y ".env.example" ".env" >nul
    echo Created .env from .env.example - edit it if you need a real API key.
)

echo.
echo Done. From repo root run start.bat or start.ps1 to launch.
endlocal
