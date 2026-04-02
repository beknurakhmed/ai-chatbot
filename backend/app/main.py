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


async def _warmup_ollama():
    """Send a tiny request to Ollama so the model is loaded into GPU memory."""
    try:
        import ollama as ollama_lib
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        client = ollama_lib.AsyncClient(host=host)
        await client.chat(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_predict": 1},
        )
        print(f"[warmup] Ollama model '{model}' loaded into GPU ✓")
    except Exception as e:
        print(f"[warmup] Ollama warmup failed (non-fatal): {e}")


async def _warmup_tts():
    """Pre-load Silero TTS models so first speech request is fast."""
    from .services.tts_service import get_silero_model
    for locale in ("uz", "ru", "en"):
        try:
            await asyncio.to_thread(get_silero_model, locale)
            print(f"[warmup] Silero TTS '{locale}' loaded ✓")
        except Exception as e:
            print(f"[warmup] Silero TTS '{locale}' failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import init_db
    await init_db()
    from .services.seed_service import seed_if_empty
    await seed_if_empty()
    from .services.knowledge_db_service import refresh
    from .services.staff_service import load_staff_cache
    await asyncio.gather(refresh(), load_staff_cache(), _warmup_ollama(), _warmup_tts())
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
