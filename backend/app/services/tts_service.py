import io
import edge_tts

VOICE_MAP = {
    "uz": {"voice": "uz-UZ-MadinaNeural", "rate": "+15%", "pitch": "+50Hz"},
    "ru": {"voice": "ru-RU-SvetlanaNeural", "rate": "+15%", "pitch": "+50Hz"},
    "en": {"voice": "en-US-JennyNeural", "rate": "+15%", "pitch": "+50Hz"},
}


async def synthesize(text: str, locale: str = "ru") -> tuple[bytes, str]:
    config = VOICE_MAP.get(locale, VOICE_MAP["ru"])

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

    return buffer.getvalue(), "audio/mpeg"
