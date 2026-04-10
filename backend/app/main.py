import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import chat, tts, admin, onboarding, survey


async def _warmup_ollama():
    try:
        import ollama as ollama_lib
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        client = ollama_lib.AsyncClient(host=host)
        await client.chat(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            options={"num_predict": 1},
            keep_alive=-1,
        )
        print(f"[warmup] Ollama model '{model}' loaded into GPU")
    except Exception as e:
        print(f"[warmup] Ollama warmup failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from .database import init_db
    await init_db()
    from .services.seed_service import seed_if_empty
    await seed_if_empty()
    from .services.knowledge_db_service import refresh
    await asyncio.gather(refresh(), _warmup_ollama())
    yield


ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:3001",
).split(",")

app = FastAPI(
    title="Uzum Onboarding",
    description="Backend API for Uzum IT employee onboarding platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(tts.router)
app.include_router(onboarding.router)
app.include_router(survey.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "healthy"}
