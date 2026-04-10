#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "============================================"
echo "  Uzum Onboarding - Local Setup (PM2)"
echo "============================================"
echo

# Check prerequisites
if ! command -v pm2 &>/dev/null; then
    echo "[INFO] Installing PM2 globally..."
    npm install -g pm2
fi

# 1. Python venv + deps
echo "[1/4] Setting up Python backend..."
if [ ! -d "backend/venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv backend/venv
fi
echo "  Installing Python dependencies..."
backend/venv/bin/pip install -q -r backend/requirements.txt
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "  Created backend/.env"
fi
echo "  [OK] Backend ready."
echo

# 2. Frontend deps
echo "[2/4] Setting up Frontend..."
if [ ! -d "frontend/node_modules" ]; then
    echo "  Installing npm dependencies..."
    (cd frontend && npm install)
else
    echo "  [OK] Dependencies exist."
fi
echo

# 3. Admin deps
echo "[3/4] Setting up Admin panel..."
if [ ! -d "admin/node_modules" ]; then
    echo "  Installing npm dependencies..."
    (cd admin && npm install)
else
    echo "  [OK] Dependencies exist."
fi
echo

# 4. Start with PM2
echo "[4/4] Starting all services with PM2..."
pm2 delete all 2>/dev/null || true
pm2 start ecosystem.config.js
echo

echo "============================================"
echo "  All services started!"
echo
echo "  Frontend:  http://localhost:3000"
echo "  Admin:     http://localhost:3001"
echo "  Backend:   http://localhost:8000"
echo
echo "  PM2 commands:"
echo "    pm2 logs          - View all logs"
echo "    pm2 status        - Check status"
echo "    pm2 restart all   - Restart all"
echo "    pm2 stop all      - Stop all"
echo "============================================"
