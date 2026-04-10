#!/bin/bash
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "  Uzum Onboarding Platform"
echo "============================================"
echo

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-3000}
ADMIN_PORT=${ADMIN_PORT:-3001}
OLLAMA_PORT=${OLLAMA_PORT:-11434}
OLLAMA_MODEL=${OLLAMA_MODEL:-qwen2.5:3b}

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}[ERROR] Docker not found. Install Docker first.${NC}"
    exit 1
fi
if ! docker info &> /dev/null; then
    echo -e "${RED}[ERROR] Docker is not running. Start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}[OK] Docker is running.${NC}"
echo

# Create .env files if missing
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}[INFO] Created .env from .env.example${NC}"
fi
if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}[INFO] Created backend/.env from .env.example${NC}"
fi
if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.example frontend/.env.local
    echo -e "${YELLOW}[INFO] Created frontend/.env.local from .env.example${NC}"
fi
if [ ! -f admin/.env.local ]; then
    cp admin/.env.example admin/.env.local
    echo -e "${YELLOW}[INFO] Created admin/.env.local from .env.example${NC}"
fi
echo

# Check/build images
echo "[1/5] Checking images..."

if ! docker image inspect uzum-backend &> /dev/null; then
    echo "  Backend image not found. Building..."
    docker compose build backend
    echo -e "  ${GREEN}[OK] Backend image built.${NC}"
else
    echo -e "  ${GREEN}[OK] Backend image exists.${NC}"
fi

if ! docker image inspect uzum-frontend &> /dev/null; then
    echo "  Frontend image not found. Building..."
    docker compose build frontend
    echo -e "  ${GREEN}[OK] Frontend image built.${NC}"
else
    echo -e "  ${GREEN}[OK] Frontend image exists.${NC}"
fi

if ! docker image inspect uzum-admin &> /dev/null; then
    echo "  Admin image not found. Building..."
    docker compose build admin
    echo -e "  ${GREEN}[OK] Admin image built.${NC}"
else
    echo -e "  ${GREEN}[OK] Admin image exists.${NC}"
fi

if ! docker image inspect ollama/ollama:latest &> /dev/null; then
    echo "  Ollama image not found. Pulling (~4GB, please wait)..."
    docker pull ollama/ollama:latest
    echo -e "  ${GREEN}[OK] Ollama image pulled.${NC}"
else
    echo -e "  ${GREEN}[OK] Ollama image exists.${NC}"
fi
echo

# Start
echo "[2/5] Starting services..."
docker compose up -d
echo

# Wait for Ollama
echo "[3/5] Waiting for Ollama..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:${OLLAMA_PORT}/api/tags > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Check/pull model
echo "  Checking LLM model..."
if ! curl -sf http://localhost:${OLLAMA_PORT}/api/tags 2>/dev/null | grep -qi "${OLLAMA_MODEL}"; then
    echo "  Model ${OLLAMA_MODEL} not found. Pulling..."
    docker exec uzum-ollama ollama pull ${OLLAMA_MODEL}
    echo -e "  ${GREEN}[OK] Model pulled.${NC}"
else
    echo -e "  ${GREEN}[OK] Model ${OLLAMA_MODEL} exists.${NC}"
fi
echo

# Wait for backend
echo "[4/5] Waiting for backend..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:${BACKEND_PORT}/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}[OK] Backend is ready!${NC}"
        break
    fi
    echo "  ... waiting ($i/60)"
    sleep 3
done
echo

# Open
echo "[5/5] Opening browser..."
echo
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  All services are running!${NC}"
echo
echo "  Frontend:  http://localhost:${FRONTEND_PORT}"
echo "  Admin:     http://localhost:${ADMIN_PORT}"
echo "  Backend:   http://localhost:${BACKEND_PORT}"
echo "  Ollama:    http://localhost:${OLLAMA_PORT}"
echo -e "${GREEN}============================================${NC}"
echo

if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:${FRONTEND_PORT} &
elif command -v open &> /dev/null; then
    open http://localhost:${FRONTEND_PORT}
fi

echo "Press Ctrl+C to stop all services..."
trap "echo; echo 'Stopping...'; docker compose down; echo 'Done.'" EXIT INT
docker compose logs -f
