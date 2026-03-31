"""AI chat service — supports Claude API, local LLM (OpenAI-compatible), and demo mode."""

import os
import re
import httpx
from anthropic import AsyncAnthropic
from .knowledge_db_service import get_knowledge_text, get_keywords_by_intent

client: AsyncAnthropic | None = None

LOCALE_INSTRUCTIONS = {
    "uz": "FAQAT O'ZBEK TILIDA javob ber. Boshqa tillarni ISHLATMA.",
    "ru": "Отвечай ТОЛЬКО НА РУССКОМ ЯЗЫКЕ. НЕ используй другие языки.",
    "en": "Reply ONLY IN ENGLISH. Do NOT use any other language.",
    "kr": "오직 한국어로만 대답하세요. 다른 언어를 사용하지 마세요.",
}

SYSTEM_PROMPT_TEMPLATE = """You are Chito, a cute mascot and assistant for Ajou University in Tashkent (AUT).

CRITICAL LANGUAGE RULE: {lang_instruction}

You are friendly, brief (2-3 sentences max), and helpful.
Use ONLY the knowledge base below to answer. If unsure, say so.
Present information exactly as given — do NOT add notes, comments, or annotations like "(repeated)", "(same as ...)", etc.

End your response with [mood:NAME] on a new line.
Moods: greeting, explaining, thinking, happy, sad, warning, studying, working, celebrating, curious

Knowledge:
{knowledge}
"""

VALID_MOODS = {
    "greeting", "explaining", "thinking", "happy", "sad", "warning",
    "studying", "working", "celebrating", "curious", "wizard",
    "birthday", "holiday", "resting", "laptop", "bottle", "soccer",
}


def get_llm_mode() -> str:
    """Determine which LLM backend to use."""
    if os.environ.get("OLLAMA_MODEL"):
        return "ollama"
    if os.environ.get("LOCAL_LLM_URL"):
        return "local"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    # Always try ollama as fallback
    return "ollama"


def get_client() -> AsyncAnthropic:
    global client
    if client is None:
        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return client


def clean_response(text: str) -> str:
    """Remove model artifacts and special tokens."""
    # Remove common LLM artifacts
    text = re.sub(r"<\|im_start\|>.*?(?:<\|im_end\|>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"<s>|</s>", "", text)
    text = text.strip()
    return text


async def build_system_prompt(locale: str, user_name: str | None = None, face_attributes: dict | None = None) -> str:
    """Build system prompt with language instruction and optional user/face context."""
    lang_instruction = LOCALE_INSTRUCTIONS.get(locale, LOCALE_INSTRUCTIONS["en"])
    knowledge = await get_knowledge_text()
    prompt = SYSTEM_PROMPT_TEMPLATE.format(lang_instruction=lang_instruction, knowledge=knowledge)
    if user_name:
        prompt += f"\n\nThe user has been identified via face recognition as: {user_name}. Address them by name when appropriate."
    if face_attributes:
        vision_parts = []
        if face_attributes.get("age"):
            vision_parts.append(f"estimated age ~{face_attributes['age']}")
        if face_attributes.get("gender"):
            g = "male" if face_attributes["gender"] == "M" else "female"
            vision_parts.append(g)
        if face_attributes.get("expression") and face_attributes["expression"] != "neutral":
            vision_parts.append(f"expression: {face_attributes['expression']}")
        if face_attributes.get("lookalike"):
            vision_parts.append(f"looks similar to celebrity: {face_attributes['lookalike']}")
        if vision_parts:
            prompt += f"\n\nYou can currently SEE the user through the camera. What you see: {', '.join(vision_parts)}."
            prompt += "\nOnly mention these observations if the user asks about their appearance, age, who they look like, etc. Do NOT volunteer this info unprompted."
    return prompt


def extract_mood(text: str) -> tuple[str, str]:
    """Extract mood tag from response text."""
    text = clean_response(text)
    match = re.search(r"\[mood:(\w+)\]", text)
    if match:
        mood = match.group(1)
        clean = text[:match.start()].strip()
        if mood in VALID_MOODS:
            return clean, mood
        return clean, "explaining"
    return text.strip(), "explaining"


async def _get_keywords(intent: str) -> list[str]:
    """Get keywords from DB for intent."""
    return await get_keywords_by_intent(intent)


_CYRILLIC_TO_LATIN = str.maketrans(
    "АВСЕНКМОРТХУаvsенкмортху",
    "ABCEHKMOPTXYabcehkmoptxy",
)


def _normalize_latin(text: str) -> str:
    """Replace look-alike Cyrillic chars with Latin equivalents."""
    return text.translate(_CYRILLIC_TO_LATIN)


def _detect_group_in_text(text: str, available_classes: list[str]) -> str | None:
    """Try to find a group name in user message."""
    text_upper = _normalize_latin(text).upper().strip()
    for cls in available_classes:
        if cls.upper() in text_upper:
            return cls
    return None


def _timetable_response(lessons: list[dict], group: str, locale: str) -> dict:
    """Return structured timetable response."""
    count = len(lessons)
    reply = {
        "en": f"Here's the schedule for {group} ({count} lessons):",
        "kr": f"{group} 시간표입니다 ({count}개 수업):",
        "uz": f"{group} dars jadvali ({count} ta dars):",
        "ru": f"Расписание {group} ({count} занятий):",
    }
    return {
        "reply": reply.get(locale, reply["en"]),
        "mood": "studying",
        "timetable": {"group": group, "lessons": lessons},
    }


async def _get_latest_news(limit: int = 5) -> list[dict]:
    """Fetch latest active news from DB."""
    from sqlalchemy import select
    from .knowledge_db_service import get_knowledge_text  # reuse session pattern
    from ..database import async_session
    from ..models.db_models import NewsItem

    try:
        async with async_session() as db:
            result = await db.execute(
                select(NewsItem)
                .where(NewsItem.is_active == True)
                .order_by(NewsItem.published_at.desc().nullslast(), NewsItem.id.desc())
                .limit(limit)
            )
            items = result.scalars().all()
            return [
                {
                    "title": n.title,
                    "url": n.url or "",
                    "date": n.published_at.strftime("%d.%m.%Y") if n.published_at else "",
                }
                for n in items
            ]
    except Exception:
        return []


def _news_response(news: list[dict], locale: str) -> dict:
    """Return structured news response."""
    header = {
        "en": f"Here are the latest news ({len(news)}):",
        "ru": f"Последние новости ({len(news)}):",
        "uz": f"So'nggi yangiliklar ({len(news)}):",
        "kr": f"최신 뉴스 ({len(news)}):",
    }
    lines = [header.get(locale, header["en"])]
    for i, n in enumerate(news, 1):
        date_part = f" ({n['date']})" if n["date"] else ""
        lines.append(f"{i}. {n['title']}{date_part}")
    return {"reply": "\n".join(lines), "mood": "explaining", "news": news}


async def chat(message: str, locale: str = "en", history: list[dict] | None = None, user_name: str | None = None, face_attributes: dict | None = None) -> dict:
    """Main chat handler with timetable integration."""
    hist = history or []
    msg_lower = message.lower()

    # Load keywords from DB
    map_keywords = await _get_keywords("map")
    timetable_keywords = await _get_keywords("timetable")
    free_room_kws = await _get_keywords("free_room")

    # Check if user is asking about map/location
    is_map_query = any(kw in msg_lower for kw in map_keywords)

    # Check if user is asking about free/empty rooms
    is_free_room_query = any(kw in msg_lower for kw in free_room_kws)

    if is_free_room_query:
        from .timetable_service import find_free_rooms
        import re as _re

        # Try to extract day
        day = ""
        for d in ["monday", "tuesday", "wednesday", "thursday", "friday",
                   "mon", "tue", "wed", "thu", "fri"]:
            if d in msg_lower:
                day = d
                break

        # Try to extract time
        time_match = _re.search(r'(\d{1,2})[:\.](\d{2})', message)
        time_str = f"{time_match.group(1)}:{time_match.group(2)}" if time_match else ""

        # Try to extract period
        period = ""
        period_match = _re.search(r'\bperiod\s*([A-G])\b', message, _re.IGNORECASE)
        if period_match:
            period = period_match.group(1).upper()

        result = await find_free_rooms(day, time_str, period)

        if result.get("available"):
            free = result["free_rooms"]
            free_by_block = result.get("free_by_block", {})
            day_code = result["day"]
            prd = result["period"]
            t = result["time"]

            if len(free) > 0:
                # Format by blocks
                block_lines = []
                for block, rooms in free_by_block.items():
                    block_label = block or "Other"
                    block_lines.append(f"{block_label}: {', '.join(rooms)}")
                block_text = "\n".join(block_lines)

                reply_text = {
                    "en": f"On {day_code} at {t} (period {prd}), {len(free)} rooms are free:\n{block_text}",
                    "ru": f"{day_code} в {t} (пара {prd}), свободно {len(free)} аудиторий:\n{block_text}",
                    "uz": f"{day_code} {t} ({prd}-dars), {len(free)} xona bo'sh:\n{block_text}",
                    "kr": f"{day_code} {t} ({prd}교시)에 {len(free)}개 교실이 비어있습니다:\n{block_text}",
                }
            else:
                reply_text = {
                    "en": f"No free rooms on {day_code} at {t} (period {prd}). All {result['total_rooms']} rooms are busy.",
                    "ru": f"Нет свободных аудиторий на {day_code} в {t} (пара {prd}). Все {result['total_rooms']} заняты.",
                    "uz": f"{day_code} {t} ({prd}-dars) da bo'sh xona yo'q. Barcha {result['total_rooms']} xona band.",
                    "kr": f"{day_code} {t}에 빈 교실이 없습니다.",
                }

            return {"reply": reply_text.get(locale, reply_text["en"]), "mood": "explaining"}

    # Check if user is asking about staff
    staff_keywords = await _get_keywords("staff")
    is_staff_query = any(kw in msg_lower for kw in staff_keywords)

    if is_staff_query:
        from .staff_service import load_staff_cache, _db_staff_cache
        if not _db_staff_cache:
            await load_staff_cache()
        if _db_staff_cache:
            staff_list = _db_staff_cache[:20]
            header = {
                "en": f"Here are the staff members ({len(staff_list)}):",
                "ru": f"Сотрудники университета ({len(staff_list)}):",
                "uz": f"Universitet xodimlari ({len(staff_list)}):",
                "kr": f"교직원 목록 ({len(staff_list)}):",
            }
            return {
                "reply": header.get(locale, header["en"]),
                "mood": "explaining",
                "staff": [{"name": s["name"], "position": s.get("position", ""), "photo": s.get("photo", "")} for s in staff_list],
            }

    # Check if user is asking about news
    news_keywords = await _get_keywords("news")
    is_news_query = any(kw in msg_lower for kw in news_keywords)

    if is_news_query:
        news = await _get_latest_news(5)
        if news:
            return _news_response(news, locale)

    # Check if user is asking about timetable
    is_timetable_query = any(kw in msg_lower for kw in timetable_keywords)

    if is_timetable_query:
        from .timetable_service import get_timetable, get_classes

        classes = await get_classes()
        group = _detect_group_in_text(message, classes)

        if not group:
            for msg in reversed(hist[-6:]):
                group = _detect_group_in_text(msg["content"], classes)
                if group:
                    break

        if group:
            tt = await get_timetable(group)
            if tt.get("available") and tt.get("lessons"):
                return _timetable_response(tt["lessons"], group, locale)
            else:
                return {"reply": f"Could not find schedule for {group}.", "mood": "thinking"}
        else:
            sample = ", ".join(classes[:10])
            ask = {
                "en": f"Which group? For example: {sample}...",
                "kr": f"어떤 그룹인가요? 예: {sample}...",
                "uz": f"Qaysi guruh? Masalan: {sample}...",
                "ru": f"Какая группа? Например: {sample}...",
            }
            return {"reply": ask.get(locale, ask["en"]), "mood": "curious"}

    # Check if message looks like a group name after bot asked
    from .timetable_service import get_classes
    classes = await get_classes()
    group = _detect_group_in_text(message, classes)
    if group:
        if hist and any(kw in hist[-1].get("content", "").lower() for kw in ["group", "guruh", "группа", "그룹", "which", "qaysi", "example", "for example"]):
            from .timetable_service import get_timetable
            tt = await get_timetable(group)
            if tt.get("available") and tt.get("lessons"):
                return _timetable_response(tt["lessons"], group, locale)

    # Regular LLM chat
    mode = get_llm_mode()

    if mode == "ollama":
        result = await chat_ollama(message, locale, hist, user_name, face_attributes)
    elif mode == "local":
        result = await chat_local(message, locale, hist, user_name, face_attributes)
    elif mode == "claude":
        result = await chat_claude(message, locale, hist, user_name, face_attributes)
    else:
        result = demo_response(message, locale)

    # Enrich with staff photos if message mentions people
    from .staff_service import find_staff_by_keywords
    staff = find_staff_by_keywords(message)
    if not staff:
        staff = find_staff_by_keywords(result.get("reply", ""))
    if staff:
        result["staff"] = [
            {"name": s["name"], "position": s["position"], "photo": s.get("photo", "")}
            for s in staff
        ]

    # Attach map if location/building question
    if is_map_query:
        result["map"] = True

    return result


async def chat_claude(message: str, locale: str, history: list[dict], user_name: str | None = None, face_attributes: dict | None = None) -> dict:
    """Chat via Claude API."""
    anthropic = get_client()
    system_prompt = await build_system_prompt(locale, user_name, face_attributes)

    messages = []
    for msg in history[-10:]:  # last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = await anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=messages,
    )

    text = response.content[0].text
    reply, mood = extract_mood(text)
    return {"reply": reply, "mood": mood}


async def chat_local(message: str, locale: str, history: list[dict], user_name: str | None = None, face_attributes: dict | None = None) -> dict:
    """Chat via local LLM (any OpenAI-compatible server: LM Studio, text-gen-webui, vLLM, etc.)."""
    base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:1234")
    model = os.environ.get("LOCAL_LLM_MODEL", "local-model")
    system_prompt = await build_system_prompt(locale, user_name, face_attributes)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
            )

        if response.status_code != 200:
            return demo_response(message, locale)

        data = response.json()
        text = data["choices"][0]["message"]["content"]
        reply, mood = extract_mood(text)
        return {"reply": reply, "mood": mood}
    except Exception:
        # Fallback to demo if local LLM is unreachable
        return demo_response(message, locale)


async def chat_ollama(message: str, locale: str, history: list[dict], user_name: str | None = None, face_attributes: dict | None = None) -> dict:
    """Chat via Ollama (local)."""
    import ollama as ollama_lib

    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    system_prompt = await build_system_prompt(locale, user_name, face_attributes)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        ollama_client = ollama_lib.AsyncClient(host=host)
        response = await ollama_client.chat(model=model, messages=messages)
        text = response["message"]["content"]
        reply, mood = extract_mood(text)
        return {"reply": reply, "mood": mood}
    except Exception:
        return demo_response(message, locale)


# --- Demo mode (keyword matching without API) ---


def demo_response(message: str, locale: str) -> dict:
    """Fallback response when LLM is unavailable."""
    defaults = {
        "uz": "Kechirasiz, hozir javob bera olmayman. Iltimos, keyinroq urinib ko'ring.",
        "ru": "Извините, сейчас не могу ответить. Пожалуйста, попробуйте позже.",
        "en": "Sorry, I can't respond right now. Please try again later.",
        "kr": "죄송합니다, 지금 응답할 수 없습니다. 나중에 다시 시도해주세요.",
    }
    return {"reply": defaults.get(locale, defaults["en"]), "mood": "sad"}
