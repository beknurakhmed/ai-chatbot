from fastapi import APIRouter, Query
from fastapi.responses import Response
from ..services.tts_service import synthesize

router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.get("")
async def tts_endpoint(
    text: str = Query(...),
    locale: str = Query(default="uz"),
):
    """Convert text to speech audio."""
    audio_bytes, media_type = await synthesize(text, locale)
    return Response(
        content=audio_bytes,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )
