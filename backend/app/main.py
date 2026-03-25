import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env — use __file__ to find backend dir
# Load .env manually since dotenv has issues with uvicorn reload on Windows
_backend_dir = Path(__file__).resolve().parent.parent
_env_file = _backend_dir / ".env"
if _env_file.exists():
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers import chat, timetable, tts, stt, face, face_ws

app = FastAPI(
    title="Chito — AUT Chatbot API",
    description="Backend API for the Ajou University in Tashkent chatbot kiosk",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve face data directory as static
faces_dir = Path(__file__).parent / "data" / "faces"
faces_dir.mkdir(parents=True, exist_ok=True)

from .database import init_db

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(chat.router)
app.include_router(timetable.router)
app.include_router(tts.router)
app.include_router(stt.router)
app.include_router(face.router)
app.include_router(face_ws.router)


@app.get("/")
async def root():
    from .services.ai_service import get_llm_mode
    return {"status": "ok", "llm_mode": get_llm_mode(), "message": "Chito AUT Chatbot API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
