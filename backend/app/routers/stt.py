from fastapi import APIRouter, UploadFile, File, Form
from ..services.stt_service import transcribe

router = APIRouter(prefix="/api/stt", tags=["stt"])


@router.post("")
async def stt_endpoint(
    audio: UploadFile = File(...),
    locale: str = Form(default="auto"),
):
    """Transcribe audio to text using Whisper."""
    audio_bytes = await audio.read()
    result = transcribe(audio_bytes, locale)
    return result
