"""
Speech-to-Text service using faster-whisper (local, GPU/CPU).
Supports: uz, ru, en, ko and auto-detection.
"""

import io
import os
import numpy as np
from faster_whisper import WhisperModel

_model: WhisperModel | None = None

LOCALE_TO_LANG = {
    "uz": "uz",
    "ru": "ru",
    "en": "en",
    "kr": "ko",
}

SUPPORTED_LANGS = {"uz", "ru", "en", "ko"}


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        import torch

        # Read WHISPER_DEVICE from environment (default: auto)
        whisper_device = os.environ.get("WHISPER_DEVICE", "auto").lower()

        # Determine device and compute_type
        if whisper_device == "cpu":
            device = "cpu"
            compute_type = "int8"
        elif whisper_device == "cuda":
            device = "cuda"
            compute_type = "float16"
        else:  # auto mode (recommended)
            if not torch.cuda.is_available():
                device = "cpu"
                compute_type = "int8"
            else:
                # Check available VRAM (in GB)
                device = "cuda"
                free_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3) - torch.cuda.memory_allocated(0) / (1024**3)

                # If less than 1.5GB free VRAM, use CPU to avoid OOM
                if free_vram_gb < 1.5:
                    print(f"[STT] Low VRAM ({free_vram_gb:.1f}GB free), falling back to CPU")
                    device = "cpu"
                    compute_type = "int8"
                else:
                    compute_type = "float16"

        _model = WhisperModel(
            "base",
            device=device,
            compute_type=compute_type,
        )
        print(f"[STT] Loaded Whisper model: device={device}, compute_type={compute_type}")
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

    detected = info.language
    # If detected language is not supported, fallback to English
    if detected not in SUPPORTED_LANGS:
        detected = "en"

    return {
        "text": text,
        "language": detected,
        "language_probability": round(info.language_probability, 2),
    }
