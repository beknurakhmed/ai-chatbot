# Uzum Onboarding Platform

Interactive chatbot kiosk for **Uzum** IT employee onboarding with voice interaction, animated mascot, and admin panel.

**Author:** Akhmedov Beknur

---

## Quick Start

```bash
git clone <repo-url>
cd uzum
./start.sh        # Linux/macOS
# or
start.bat         # Windows
```

The script creates config files, builds Docker images, and starts all services.

**Services after startup:**
| Service | URL |
|---------|-----|
| Frontend (Kiosk) | http://localhost:3000 |
| Admin Panel | http://localhost:3001 |
| Backend API | http://localhost:8000 |
| Ollama LLM | http://localhost:11434 |

**Admin login token:** set in `.env` (`ADMIN_TOKEN`)

---

## Features

### Chat
- Local LLM via Ollama (qwen2.5:7b default), with optional Claude API fallback
- Knowledge base Q&A from database
- Intent detection with configurable keywords
- Mood system with animated mascot (Uzumchi)
- Multi-language: Uzbek, Russian, English

### Voice
- TTS: Edge TTS (uz/ru/en)
- Auto-speak responses

### Onboarding
- Structured checklist (day 1, week 1, week 2, month 1)
- Employee progress tracking
- Pulse surveys for well-being monitoring

### Admin Panel
- Dashboard with real-time stats
- CRUD for: Knowledge Base, Keywords, Onboarding Tasks, Departments
- Interaction logs and analytics
- Dark/Light mode

---

## Architecture

```
uzum/
├── backend/          # FastAPI + Python services
│   ├── app/
│   │   ├── main.py           # App entry, lifespan
│   │   ├── database.py       # Async SQLAlchemy
│   │   ├── models/           # Pydantic schemas + DB models
│   │   ├── routers/          # API endpoints
│   │   └── services/         # Chat, TTS, knowledge, seeding
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # Next.js 16 kiosk interface
│   ├── src/
│   │   ├── app/              # Pages
│   │   ├── components/       # UI components
│   │   ├── hooks/            # Custom hooks
│   │   ├── i18n/             # Translations (uz/ru/en)
│   │   └── lib/              # API client, store
│   └── Dockerfile
├── admin/            # Next.js 14 admin panel
│   ├── src/
│   │   ├── app/              # CRUD pages
│   │   ├── components/       # Shared UI (DataTable, Modal, Theme)
│   │   └── lib/              # API client
│   └── Dockerfile
├── docker-compose.yml
├── start.sh / start.bat
└── .env.example
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy 2.0 (async), Python 3.12 |
| Database | PostgreSQL 16 |
| LLM | Ollama (qwen2.5) |
| TTS | Edge TTS |
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Zustand |
| Admin | Next.js 14, React 18, Tailwind CSS 3, Sonner |
| Infra | Docker Compose, NVIDIA GPU support |

---

## Environment Configuration

All config is via `.env.example` files. On first `start.sh`, they're auto-copied to `.env` / `.env.local`.

### Root `.env`
```bash
BACKEND_PORT=8000
FRONTEND_PORT=3000
ADMIN_PORT=3001
POSTGRES_PORT=5432
OLLAMA_PORT=11434
POSTGRES_USER=uzum
POSTGRES_PASSWORD=change-me-in-production
POSTGRES_DB=uzum
ADMIN_TOKEN=change-me-in-production
OLLAMA_MODEL=qwen2.5:7b
```

### Backend `backend/.env`
```bash
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_HOST=http://ollama:11434
# ANTHROPIC_API_KEY=sk-ant-...    # Optional: enables Claude
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Frontend `frontend/.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Admin `admin/.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Endpoints

### Public
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/chat` | Send message to chatbot |
| GET | `/api/tts` | Text-to-speech |
| GET | `/api/onboarding/tasks` | List onboarding tasks |
| GET | `/api/onboarding/progress/{name}` | Employee progress |
| POST | `/api/onboarding/complete` | Mark task done |
| POST | `/api/survey` | Submit pulse survey |
| GET | `/api/survey/{name}` | Survey history |

### Admin (Bearer token required)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/stats` | Dashboard statistics |
| GET/POST/PUT/DELETE | `/admin/knowledge[/{id}]` | Knowledge base CRUD |
| POST | `/admin/knowledge/refresh-cache` | Reload knowledge cache |
| POST | `/admin/knowledge/reseed` | Reseed from defaults |
| GET/POST/PUT/DELETE | `/admin/keywords[/{id}]` | Keywords CRUD |
| GET/POST/PUT/DELETE | `/admin/onboarding-tasks[/{id}]` | Onboarding tasks CRUD |
| GET/POST/PUT/DELETE | `/admin/departments[/{id}]` | Departments CRUD |
| GET | `/admin/logs` | Interaction logs |

---

## Database Schema

| Table | Key Fields |
|-------|-----------|
| `knowledge_entries` | category, title, content, language, is_active |
| `keywords` | keyword, intent, language, is_active |
| `onboarding_tasks` | title, description, category, order_num |
| `departments` | name, description, head_name |
| `employee_onboarding` | employee_name, task_id, is_completed |
| `pulse_surveys` | employee_name, mood_score, comment, category |
| `interaction_logs` | employee_name, message, reply, locale, mood |

---

## Docker Services

| Service | Image | Port | GPU |
|---------|-------|------|-----|
| postgres | postgres:16 | 5432 | No |
| ollama | ollama/ollama:latest | 11434 | Yes |
| backend | Custom (Python 3.12) | 8000 | No |
| frontend | Custom (Node 22 Alpine) | 3000 | No |
| admin | Custom (Node 22 Alpine) | 3001 | No |

**Persistent volumes:** postgres-data, ollama-models

---

## Production Deployment

1. Clone and configure:
```bash
git clone <repo-url>
cd uzum
cp .env.example .env
```

2. Edit `.env` with production settings — **change all default passwords and tokens**.

3. Set backend URL for frontend/admin:
```bash
echo "NEXT_PUBLIC_API_URL=https://api.yourdomain.uz" > frontend/.env.local
echo "NEXT_PUBLIC_API_URL=http://internal-ip:8000" > admin/.env.local
```

4. Build and start:
```bash
docker compose build
docker compose up -d
```

5. Initialize data via admin panel at http://localhost:3001

---

## Development (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Admin
cd admin
npm install
npm run dev -- -p 3001
```

Or with PM2:
```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

---

## Requirements

- **Docker** + Docker Compose
- **NVIDIA GPU** with CUDA drivers (for LLM inference via Ollama)
  - Minimum 6GB VRAM (use qwen2.5:3b)
  - Recommended 8GB+ VRAM (qwen2.5:7b)
- **Internet** for first run (downloads models)

---

## License

This project was developed for Uzum hakaton

**Author:** Akhmedov Beknur
