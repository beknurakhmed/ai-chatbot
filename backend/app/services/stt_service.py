"""
Speech-to-Text service using faster-whisper (local, GPU).
Supports: uz, ru, en, ko and auto-detection.
"""

import io
import numpy as np
from faster_whisper import WhisperModel

_model: WhisperModel | None = None

LOCALE_TO_LANG = {
    "uz": "uz",
    "ru": "ru",
    "en": "en",
    "kr": "ko",
}


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            "base",
            device="cuda",
            compute_type="float16",
        )
    return _model


def transcribe(audio_bytes: bytes, locale: str = "auto") -> dict:
    """
    Transcribe audio bytes to text.
    Audio can be WAV, WebM, OGG, MP3, etc.
    Returns: {"text": str, "language": str}
    """
    model = get_model()

    lang = LOCALE_TO_LANG.get(locale)

    segments, info = model.transcribe(
        io.BytesIO(audio_bytes),
        language=lang,  # None = auto-detect
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    text = " ".join(seg.text.strip() for seg in segments)

    return {
        "text": text,
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
    }
