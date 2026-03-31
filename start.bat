@echo off
chcp 65001 >nul 2>&1
title AUT Chatbot - Chito
cd /d "%~dp0"

echo ============================================
echo   Chito - AUT Kiosk Chatbot
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
setlocal enabledelayedexpansion

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
    copy frontend\.env.example frontend\.env.local >nul
    echo [INFO] Created frontend\.env.local from .env.example
)
if not exist admin\.env.local (
    copy admin\.env.example admin\.env.local >nul
    echo [INFO] Created admin\.env.local from .env.example
)
echo.

:: Check if images exist, build if not
echo [1/5] Checking images...

docker image inspect aut-backend >nul 2>&1
if %errorlevel% neq 0 (
    echo   Backend image not found. Building...
    docker compose build backend
    if %errorlevel% neq 0 (
        echo [ERROR] Backend build failed.
        pause
        exit /b 1
    )
    echo   [OK] Backend image built.
) else (
    echo   [OK] Backend image exists.
)

docker image inspect aut-frontend >nul 2>&1
if %errorlevel% neq 0 (
    echo   Frontend image not found. Building...
    docker compose build frontend
    if %errorlevel% neq 0 (
        echo [ERROR] Frontend build failed.
        pause
        exit /b 1
    )
    echo   [OK] Frontend image built.
) else (
    echo   [OK] Frontend image exists.
)

docker image inspect aut-admin >nul 2>&1
if %errorlevel% neq 0 (
    echo   Admin image not found. Building...
    docker compose build admin
    if %errorlevel% neq 0 (
        echo [ERROR] Admin build failed.
        pause
        exit /b 1
    )
    echo   [OK] Admin image built.
) else (
    echo   [OK] Admin image exists.
)

docker image inspect ollama/ollama:latest >nul 2>&1
if %errorlevel% neq 0 (
    echo   Ollama image not found. Pulling (~4GB, please wait)...
    docker pull ollama/ollama:latest
    if %errorlevel% neq 0 (
        echo [ERROR] Ollama pull failed.
        pause
        exit /b 1
    )
    echo   [OK] Ollama image pulled.
) else (
    echo   [OK] Ollama image exists.
)
echo.

:: Start services
echo [2/5] Starting services...
docker compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] docker compose up failed.
    pause
    exit /b 1
)
echo.

:: Wait for Ollama
echo [3/5] Waiting for Ollama...
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
:: Check if model exists, pull if not
echo   Checking LLM model...
curl -sf http://localhost:%OLLAMA_PORT%/api/tags 2>nul | findstr /i "%OLLAMA_MODEL%" >nul 2>&1
if %errorlevel% neq 0 (
    echo   Model %OLLAMA_MODEL% not found. Pulling...
    docker exec aut-ollama ollama pull %OLLAMA_MODEL%
    echo   [OK] Model pulled.
) else (
    echo   [OK] Model %OLLAMA_MODEL% exists.
)
echo.

:: Wait for backend
echo [4/5] Waiting for backend...
set /a tries=0
:wait_backend
if %tries% geq 60 (
    echo   [WARN] Backend still starting. First run downloads InsightFace model (~300MB).
    echo          Check: docker compose logs -f backend
    goto open
)
timeout /t 3 /nobreak >nul
curl -sf http://localhost:%BACKEND_PORT%/health >nul 2>&1
if %errorlevel% equ 0 goto backend_ready
set /a tries+=1
echo   ... waiting (%tries%/60)
goto wait_backend

:backend_ready
echo   [OK] Backend is ready!
echo.

:open
echo [5/5] Opening browser...
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
