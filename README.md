# Chito - AUT AI Chatbot Kiosk

AI-powered interactive chatbot kiosk for **Ajou University in Tashkent (AUT)** with face recognition, voice interaction, and campus information services.

**Author:** Akhmedov Beknur | ECE Department | Ajou University in Tashkent

---

## Quick Start

```bash
git clone https://github.com/beknurakhmed/ai-chatbot.git
cd ai-chatbot
./start.sh        # Linux/macOS
# or
start.bat         # Windows
```

That's it. The script creates config files, builds Docker images, and starts all services.

**Services after startup:**
| Service | URL |
|---------|-----|
| Frontend (Kiosk) | http://localhost:3000 |
| Admin Panel | http://localhost:3001 |
| Backend API | http://localhost:8000 |
| Ollama LLM | http://localhost:11434 |

**Admin login token:** `chito-admin-secret` (change in `.env`)

---

## Features

### AI Chat
- Local LLM via Ollama (qwen2.5:7b default) or Claude API
- Knowledge base Q&A from database
- Intent detection with configurable keywords
- Mood system with animated mascot (Chito)
- Multi-language: Uzbek, Russian, English, Korean

### Face Recognition
- Real-time face detection via InsightFace (512-dim embeddings)
- User registration & recognition with pgvector similarity search
- Age, gender, expression analysis
- Celebrity lookalike matching

### Voice Interaction
- STT: Faster Whisper (local, GPU/CPU auto-detect)
- TTS: Silero (uz/ru/en) + Edge TTS fallback (kr)
- Auto-speak AI responses

### Campus Services
- Class timetable lookup (synced from aut.edupage.org)
- Free classroom finder (by day/time/period, grouped by block)
- Campus map with building legend
- Staff directory with photos
- University news feed
- Room/block management

### Kiosk Mode
- Auto-sleep after idle timeout
- Wake on face detection
- Configurable via environment variables

### Admin Panel
- Dashboard with real-time stats
- CRUD for: Knowledge Base, Keywords, News, Staff, Timetable, Buildings, Rooms
- Data sync from external sources (ajou.uz, edupage.org)
- Dark/Light mode
- Toast notifications

---

## Architecture

```
ai-chatbot/
├── backend/          # FastAPI + Python AI services
│   ├── app/
│   │   ├── main.py           # App entry, lifespan
│   │   ├── database.py       # Async SQLAlchemy + pgvector
│   │   ├── models/           # Pydantic schemas + DB models
│   │   ├── routers/          # API endpoints
│   │   └── services/         # AI, TTS, STT, face, timetable
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # Next.js 16 kiosk interface
│   ├── src/
│   │   ├── app/              # Pages
│   │   ├── components/       # UI components
│   │   ├── hooks/            # Custom hooks
│   │   ├── i18n/             # Translations (uz/ru/en/kr)
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
| Backend | FastAPI, SQLAlchemy 2.0 (async), Python 3.11+ |
| Database | PostgreSQL 16 + pgvector |
| LLM | Ollama (qwen2.5) / Claude API |
| Face AI | InsightFace + pgvector similarity |
| STT | Faster Whisper |
| TTS | Silero TTS + Edge TTS |
| Frontend | Next.js 16, React 19, Tailwind CSS 4, Zustand |
| Admin | Next.js 14, React 18, Tailwind CSS 3, Sonner |
| Infra | Docker Compose, NVIDIA GPU support |

---

## Environment Configuration

All config is via `.env.example` files. On first `start.sh`, they're auto-copied to `.env` / `.env.local`.

### Root `.env`
```bash
BACKEND_PORT=8000          # Backend API port
FRONTEND_PORT=3000         # Kiosk frontend port
ADMIN_PORT=3001            # Admin panel port
POSTGRES_PORT=5432         # PostgreSQL port
OLLAMA_PORT=11434          # Ollama LLM port
POSTGRES_USER=chito        # DB username
POSTGRES_PASSWORD=chito    # DB password
POSTGRES_DB=chito          # DB name
ADMIN_TOKEN=chito-admin-secret  # Admin auth token
OLLAMA_MODEL=qwen2.5:7b   # LLM model
```

### Backend `backend/.env`
```bash
OLLAMA_MODEL=qwen2.5:7b           # LLM model name
OLLAMA_HOST=http://ollama:11434    # Ollama host (docker internal)
# ANTHROPIC_API_KEY=sk-ant-...    # Optional: Claude API
WHISPER_DEVICE=auto                # STT device: auto/cpu/cuda
WHISPER_MODEL=base                 # STT model size
```

### Frontend `frontend/.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend URL
NEXT_PUBLIC_LANGUAGES=uz,ru,en,kr         # Enabled languages
NEXT_PUBLIC_KIOSK_SLEEP_MODE_ENABLED=false
NEXT_PUBLIC_KIOSK_IDLE_TIMEOUT=10000      # ms before sleep
NEXT_PUBLIC_KIOSK_WAKE_THRESHOLD=3        # face detections to wake
```

### Admin `admin/.env.local`
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend URL
```

---

## API Endpoints

### Public
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/chat` | Send message to chatbot |
| GET | `/api/buildings` | Campus buildings for map |
| GET | `/api/timetable` | Get group timetable |
| GET | `/api/timetable/classes` | List all groups |
| GET | `/api/timetable/teachers` | List all teachers |
| GET | `/api/timetable/subjects` | List all subjects |
| GET | `/api/timetable/free-rooms` | Find free classrooms |
| GET | `/api/tts` | Text-to-speech |
| POST | `/api/stt` | Speech-to-text |
| GET | `/api/face/list` | List registered faces |
| POST | `/api/face/save` | Register face |
| WS | `/ws/face` | Real-time face analysis |

### Admin (Bearer token required)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/stats` | Dashboard statistics |
| GET/POST/PUT/DELETE | `/admin/knowledge[/{id}]` | Knowledge base CRUD |
| POST | `/admin/knowledge/refresh-cache` | Reload knowledge cache |
| GET/POST/PUT/DELETE | `/admin/keywords[/{id}]` | Keywords CRUD |
| GET/POST/PUT/DELETE | `/admin/news[/{id}]` | News CRUD |
| POST | `/admin/news/refresh` | Fetch from ajou.uz |
| GET/POST/PUT/DELETE | `/admin/staff[/{id}]` | Staff CRUD |
| POST | `/admin/staff/refresh` | Parse from ajou.uz |
| GET/POST/PUT/DELETE | `/admin/timetable[/{id}]` | Timetable CRUD |
| POST | `/admin/timetable/refresh` | Sync from edupage.org |
| GET/POST/PUT/DELETE | `/admin/buildings[/{id}]` | Buildings CRUD |
| GET/POST/PUT/DELETE | `/admin/rooms[/{id}]` | Rooms CRUD |
| POST | `/admin/rooms/sync` | Extract rooms from timetable |
| GET | `/admin/logs` | Interaction logs |

---

## Database Schema

| Table | Key Fields |
|-------|-----------|
| `knowledge_entries` | category, title, content, language, is_active |
| `keywords` | keyword, intent, language, is_active |
| `timetable_entries` | group, day, period, time_str, subject, teacher, room |
| `staff_members` | name, position, photo, category |
| `rooms` | name, block, floor, capacity |
| `buildings` | num, name, description, color |
| `news_items` | title, content, url, image_url, published_at |
| `known_faces` | name, embedding (vector 512), age, gender |
| `celebrity_faces` | name, embedding (vector 512) |
| `interaction_logs` | user_name, message, reply, locale, mood |

---

## Docker Services

| Service | Image | Port | GPU |
|---------|-------|------|-----|
| postgres | pgvector/pgvector:pg16 | 5432 | No |
| ollama | ollama/ollama:latest | 11434 | Yes |
| backend | Custom (PyTorch + CUDA) | 8000 | Yes |
| frontend | Custom (Node 22 Alpine) | 3000 | No |
| admin | Custom (Node 22 Alpine) | 3001 | No |

**Persistent volumes:** postgres-data, ollama-models, insightface-models

---

## Production Deployment

1. Clone and configure:
```bash
git clone https://github.com/beknurakhmed/ai-chatbot.git
cd ai-chatbot
cp .env.example .env
```

2. Edit `.env` with production settings (ports, passwords, model).

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

5. Initialize data via admin panel:
   - Login at http://localhost:3001 with admin token
   - Timetable > "Refresh from edupage"
   - Staff > "Refresh from ajou.uz"
   - News > "Refresh"
   - Rooms > "Sync from timetable"

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
- **NVIDIA GPU** with CUDA drivers (for LLM + face recognition + STT)
  - Minimum 6GB VRAM (use qwen2.5:3b)
  - Recommended 8GB+ VRAM (qwen2.5:7b)
- **Internet** for first run (downloads models ~12GB total)

---

## License

This project was developed as a graduation project at Ajou University in Tashkent.

**Author:** Akhmedov Beknur
**Department:** Electrical & Computer Engineering (ECE)
**GitHub:** https://github.com/beknurakhmed
**LinkedIn:** https://www.linkedin.com/in/beknur-akhmedov-6716292b4/
**Website:** https://www.beknurdev.uz/
