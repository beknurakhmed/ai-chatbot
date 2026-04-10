@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title Uzum Onboarding Platform
cd /d "%~dp0"

echo ============================================
echo   Uzum Onboarding Platform
echo ============================================
echo.

:: Load .env
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
        set "line=%%a"
        if not "!line:~0,1!"=="#" (
            if not "%%a"=="" set "%%a=%%b"
        )
    )
)

:: Defaults
if not defined BACKEND_PORT set BACKEND_PORT=8000
if not defined FRONTEND_PORT set FRONTEND_PORT=3000
if not defined ADMIN_PORT set ADMIN_PORT=3001
if not defined OLLAMA_PORT set OLLAMA_PORT=11434
if not defined OLLAMA_MODEL set OLLAMA_MODEL=qwen2.5:3b

:: Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found. Install Docker Desktop first.
    pause
    exit /b 1
)
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Start Docker Desktop first.
    pause
    exit /b 1
)
echo [OK] Docker is running.
echo.

:: Create .env files if missing
if not exist .env (
    copy .env.example .env >nul
    echo [INFO] Created .env from .env.example
)
if not exist backend\.env (
    copy backend\.env.example backend\.env >nul
    echo [INFO] Created backend\.env from .env.example
)
if not exist frontend\.env.local (
    copy frontend\.env.example frontend\.env.local >nul 2>nul
    echo [INFO] Created frontend\.env.local
)
if not exist admin\.env.local (
    copy admin\.env.example admin\.env.local >nul 2>nul
    echo [INFO] Created admin\.env.local
)
echo.

:: Build and start
echo [1/4] Building and starting services...
docker compose up --build -d
if %errorlevel% neq 0 (
    echo [ERROR] docker compose up failed.
    pause
    exit /b 1
)
echo.

:: Wait for Ollama
echo [2/4] Waiting for Ollama...
set /a tries=0
:wait_ollama
if %tries% geq 30 (
    echo   [WARN] Ollama slow to start, continuing...
    goto pull_model
)
timeout /t 2 /nobreak >nul
curl -sf http://localhost:%OLLAMA_PORT%/api/tags >nul 2>&1
if %errorlevel% equ 0 goto pull_model
set /a tries+=1
goto wait_ollama

:pull_model
echo   Checking LLM model...
curl -sf http://localhost:%OLLAMA_PORT%/api/tags 2>nul | findstr /i "%OLLAMA_MODEL%" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Model %OLLAMA_MODEL% not found. Pulling...
    docker exec uzum-ollama ollama pull %OLLAMA_MODEL%
    echo   [OK] Model pulled.
) else (
    echo   [OK] Model %OLLAMA_MODEL% exists.
)
echo.

:: Wait for backend
echo [3/4] Waiting for backend...
set /a tries=0
:wait_backend
if %tries% geq 30 (
    echo   [WARN] Backend still starting...
    echo          Check: docker compose logs -f backend
    goto open
)
timeout /t 3 /nobreak >nul
curl -sf http://localhost:%BACKEND_PORT%/health >nul 2>&1
if %errorlevel% equ 0 goto backend_ready
set /a tries+=1
echo   ... waiting (%tries%/30)
goto wait_backend

:backend_ready
echo   [OK] Backend is ready!
echo.

:open
echo [4/4] Opening browser...
echo.
echo ============================================
echo   All services are running!
echo.
echo   Frontend:  http://localhost:%FRONTEND_PORT%
echo   Admin:     http://localhost:%ADMIN_PORT%
echo   Backend:   http://localhost:%BACKEND_PORT%
echo   Ollama:    http://localhost:%OLLAMA_PORT%
echo ============================================
echo.
start http://localhost:%FRONTEND_PORT%

echo Press any key to STOP all services...
pause >nul

echo.
echo Stopping all services...
docker compose down
echo Done.
pause
