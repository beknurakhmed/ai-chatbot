"""
Text-to-Speech service.
- Silero TTS for uz, ru, en (local, offline)
- edge-tts fallback for kr (cloud)
"""

import io
import torch
import edge_tts

_silero_models: dict = {}

# Silero model configs per language
SILERO_CONFIG = {
    "ru": {"model_id": "v4_ru", "speaker": "baya_v2", "sample_rate": 48000},
    "en": {"model_id": "v3_en", "speaker": "lj_v2", "sample_rate": 48000},
    "uz": {"model_id": "v4_uz", "speaker": "dilnavoz_v2", "sample_rate": 48000},
}

# edge-tts fallback for Korean
EDGE_VOICE_MAP = {
    "kr": {"voice": "ko-KR-SunHiNeural", "rate": "+20%", "pitch": "+45Hz"},
}


def get_silero_model(locale: str):
    """Load Silero TTS model (cached)."""
    if locale in _silero_models:
        return _silero_models[locale]

    config = SILERO_CONFIG.get(locale)
    if not config:
        return None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model, _ = torch.hub.load(
        repo_or_dir="snakers4/silero-models",
        model="silero_tts",
        language=locale if locale != "uz" else "uz",
        speaker=config["speaker"],
    )
    model = model.to(device)
    _silero_models[locale] = (model, config)
    return (model, config)


def silero_synthesize(text: str, locale: str) -> bytes:
    """Synthesize with Silero TTS. Returns WAV bytes."""
    result = get_silero_model(locale)
    if result is None:
        raise ValueError(f"No Silero model for {locale}")

    model, config = result

    audio = model.apply_tts(
        text=text,
        speaker=config["speaker"],
        sample_rate=config["sample_rate"],
    )

    # Convert to WAV bytes
    buffer = io.BytesIO()
    import wave
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(config["sample_rate"])
        # Convert float tensor to int16
        audio_np = (audio.cpu().numpy() * 32767).astype("int16")
        wf.writeframes(audio_np.tobytes())

    return buffer.getvalue()


async def edge_synthesize(text: str, locale: str) -> bytes:
    """Synthesize with edge-tts (cloud fallback)."""
    config = EDGE_VOICE_MAP.get(locale, EDGE_VOICE_MAP["kr"])

    communicate = edge_tts.Communicate(
        text,
        config["voice"],
        rate=config["rate"],
        pitch=config["pitch"],
    )

    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    return buffer.getvalue()


async def synthesize(text: str, locale: str = "uz") -> tuple[bytes, str]:
    """
    Convert text to speech.
    Returns: (audio_bytes, media_type)
    """
    # Korean → edge-tts (cloud)
    if locale == "kr":
        audio = await edge_synthesize(text, locale)
        return audio, "audio/mpeg"

    # uz, ru, en → Silero (local)
    if locale in SILERO_CONFIG:
        try:
            audio = silero_synthesize(text, locale)
            return audio, "audio/wav"
        except Exception as e:
            print(f"Silero TTS failed for {locale}: {e}, falling back to edge-tts")

    # Fallback: edge-tts for any language (higher pitch for child-like sound)
    fallback_voices = {
        "uz": {"voice": "uz-UZ-MadinaNeural", "rate": "+15%", "pitch": "+50Hz"},
        "ru": {"voice": "ru-RU-SvetlanaNeural", "rate": "+12%", "pitch": "+45Hz"},
        "en": {"voice": "en-US-AnaNeural", "rate": "+10%", "pitch": "+40Hz"},
        "kr": {"voice": "ko-KR-SunHiNeural", "rate": "+12%", "pitch": "+45Hz"},
    }
    config = fallback_voices.get(locale, fallback_voices["en"])
    communicate = edge_tts.Communicate(text, config["voice"], rate=config["rate"], pitch=config["pitch"])
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue(), "audio/mpeg"
