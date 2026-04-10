@echo off
chcp 65001 >nul 2>&1
title Uzum Onboarding - PM2
cd /d "%~dp0"

echo ============================================
echo   Uzum Onboarding - Local Setup (PM2)
echo ============================================
echo.

:: Check prerequisites
where pm2 >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing PM2 globally...
    npm install -g pm2
)

:: 1. Python venv + deps
echo [1/4] Setting up Python backend...
if not exist backend\venv (
    echo   Creating virtual environment...
    python -m venv backend\venv
)
echo   Installing Python dependencies...
backend\venv\Scripts\pip install -q -r backend\requirements.txt
if not exist backend\.env (
    copy backend\.env.example backend\.env >nul
    echo   Created backend\.env
)
echo   [OK] Backend ready.
echo.

:: 2. Frontend deps
echo [2/4] Setting up Frontend...
if not exist frontend\node_modules (
    echo   Installing npm dependencies...
    cd frontend && npm install && cd ..
) else (
    echo   [OK] Dependencies exist.
)
echo.

:: 3. Admin deps
echo [3/4] Setting up Admin panel...
if not exist admin\node_modules (
    echo   Installing npm dependencies...
    cd admin && npm install && cd ..
) else (
    echo   [OK] Dependencies exist.
)
echo.

:: 4. Start with PM2
echo [4/4] Starting all services with PM2...
pm2 delete all >nul 2>&1
pm2 start ecosystem.config.js
echo.

echo ============================================
echo   All services started!
echo.
echo   Frontend:  http://localhost:3000
echo   Admin:     http://localhost:3001
echo   Backend:   http://localhost:8000
echo.
echo   PM2 commands:
echo     pm2 logs          - View all logs
echo     pm2 status        - Check status
echo     pm2 restart all   - Restart all
echo     pm2 stop all      - Stop all
echo ============================================
echo.
start http://localhost:3000
echo Press any key to stop all services...
pause >nul
pm2 stop all
echo Done.
pause
