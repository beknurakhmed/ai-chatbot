import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
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
from .routers import chat, timetable, tts, stt, face, face_ws, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import init_db
    await init_db()
    from .services.seed_service import seed_if_empty
    await seed_if_empty()
    from .services.knowledge_db_service import refresh
    from .services.staff_service import load_staff_cache
    await asyncio.gather(refresh(), load_staff_cache())
    yield


app = FastAPI(
    title="Chito — AUT Chatbot API",
    description="Backend API for the Ajou University in Tashkent chatbot kiosk",
    version="0.2.0",
    lifespan=lifespan,
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

app.include_router(chat.router)
app.include_router(timetable.router)
app.include_router(tts.router)
app.include_router(stt.router)
app.include_router(face.router)
app.include_router(face_ws.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}
