#!/bin/bash
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "============================================"
echo "  Chito - AUT Kiosk Chatbot"
echo "============================================"
echo

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

# Check/build images
echo "[1/5] Checking images..."

if ! docker image inspect aut-backend &> /dev/null; then
    echo "  Backend image not found. Building..."
    docker compose build backend
    echo -e "  ${GREEN}[OK] Backend image built.${NC}"
else
    echo -e "  ${GREEN}[OK] Backend image exists.${NC}"
fi

if ! docker image inspect aut-frontend &> /dev/null; then
    echo "  Frontend image not found. Building..."
    docker compose build frontend
    echo -e "  ${GREEN}[OK] Frontend image built.${NC}"
else
    echo -e "  ${GREEN}[OK] Frontend image exists.${NC}"
fi

if ! docker image inspect aut-admin &> /dev/null; then
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
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

# Check/pull model
echo "  Checking LLM model..."
if ! curl -sf http://localhost:11434/api/tags 2>/dev/null | grep -qi "qwen2.5:7b"; then
    echo "  Model qwen2.5:7b not found. Pulling (~4.7GB, please wait)..."
    docker exec aut-ollama ollama pull qwen2.5:7b
    echo -e "  ${GREEN}[OK] Model pulled.${NC}"
else
    echo -e "  ${GREEN}[OK] Model qwen2.5:7b exists.${NC}"
fi
echo

# Wait for backend
echo "[4/5] Waiting for backend..."
for i in $(seq 1 60); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
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
echo "  Frontend:  http://localhost:3000"
echo "  Admin:     http://localhost:3001"
echo "  Backend:   http://localhost:8000"
echo "  Ollama:    http://localhost:11434"
echo -e "${GREEN}============================================${NC}"
echo

if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &
elif command -v open &> /dev/null; then
    open http://localhost:3000
fi

echo "Press Ctrl+C to stop all services..."
trap "echo; echo 'Stopping...'; docker compose down; echo 'Done.'" EXIT INT
docker compose logs -f
