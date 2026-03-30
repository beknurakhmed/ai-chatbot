"""AI chat service — supports Claude API, local LLM (OpenAI-compatible), and demo mode."""

import os
import re
import httpx
from anthropic import Anthropic
from .knowledge_base import get_knowledge

client: Anthropic | None = None

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


def get_client() -> Anthropic:
    global client
    if client is None:
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return client


def clean_response(text: str) -> str:
    """Remove model artifacts and special tokens."""
    # Remove common LLM artifacts
    text = re.sub(r"<\|im_start\|>.*?(?:<\|im_end\|>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"<s>|</s>", "", text)
    text = text.strip()
    return text


def build_system_prompt(locale: str, user_name: str | None = None, face_attributes: dict | None = None) -> str:
    """Build system prompt with language instruction and optional user/face context."""
    lang_instruction = LOCALE_INSTRUCTIONS.get(locale, LOCALE_INSTRUCTIONS["en"])
    knowledge = get_knowledge()
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


TIMETABLE_KEYWORDS = [
    "timetable", "schedule", "расписание", "пары", "dars", "jadval",
    "시간표", "수업", "lesson", "class schedule", "when", "what class",
]

MAP_KEYWORDS = [
    "map", "campus map", "where is", "location", "building", "how to get",
    "карта", "где находится", "здание", "корпус",
    "xarita", "qayerda", "bino",
    "지도", "어디", "건물",
]


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


async def chat(message: str, locale: str = "en", history: list[dict] | None = None, user_name: str | None = None, face_attributes: dict | None = None) -> dict:
    """Main chat handler with timetable integration."""
    hist = history or []
    msg_lower = message.lower()

    # Check if user is asking about map/location
    is_map_query = any(kw in msg_lower for kw in MAP_KEYWORDS)

    # Check if user is asking about free/empty rooms
    FREE_ROOM_KEYWORDS = ["free room", "empty room", "available room", "free class",
                          "empty class", "свободн", "пустой", "bo'sh xona",
                          "빈 교실", "which room is free", "vacant"]
    is_free_room_query = any(kw in msg_lower for kw in FREE_ROOM_KEYWORDS)

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
            day_code = result["day"]
            prd = result["period"]
            t = result["time"]

            if len(free) > 0:
                rooms_list = ", ".join(free[:15])
                more = f" (+{len(free)-15} more)" if len(free) > 15 else ""
                reply_text = {
                    "en": f"On {day_code} at {t} (period {prd}), {len(free)} rooms are free:\n{rooms_list}{more}",
                    "kr": f"{day_code} {t} ({prd}교시)에 {len(free)}개 교실이 비어있습니다:\n{rooms_list}{more}",
                }
            else:
                reply_text = {
                    "en": f"No free rooms on {day_code} at {t} (period {prd}). All {result['total_rooms']} rooms are busy.",
                    "kr": f"{day_code} {t}에 빈 교실이 없습니다.",
                }

            return {"reply": reply_text.get(locale, reply_text["en"]), "mood": "explaining"}

    # Check if user is asking about timetable
    is_timetable_query = any(kw in msg_lower for kw in TIMETABLE_KEYWORDS)

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
    system_prompt = build_system_prompt(locale, user_name, face_attributes)

    messages = []
    for msg in history[-10:]:  # last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    response = anthropic.messages.create(
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
    system_prompt = build_system_prompt(locale, user_name, face_attributes)

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
    system_prompt = build_system_prompt(locale, user_name, face_attributes)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        response = ollama_lib.chat(model=model, messages=messages)
        text = response["message"]["content"]
        reply, mood = extract_mood(text)
        return {"reply": reply, "mood": mood}
    except Exception:
        return demo_response(message, locale)


# --- Demo mode (keyword matching without API) ---

DEMO_KEYWORDS = {
    "uz": {
        "greeting": {
            "keywords": ["salom", "hey", "assalom", "hayrli"],
            "reply": "Salom! Men Chito — AUT yordamchisiman! Sizga qanday yordam bera olaman?",
        },
        "rector": {
            "keywords": ["rektor", "rector"],
            "reply": "Rektor kabineti 3-qavatda, 301-xonada joylashgan. Asosiy zinapoyadan yuqoriga chiqing va o'ngga buriling.",
            "mood": "explaining",
        },
        "library": {
            "keywords": ["kutubxona", "library", "kitob"],
            "reply": "Kutubxona 2-qavatda joylashgan. U dushanba-juma kunlari 9:00-18:00 gacha ishlaydi.",
            "mood": "studying",
        },
        "cafeteria": {
            "keywords": ["oshxona", "ovqat", "cafeteria", "tushlik"],
            "reply": "Oshxona 1-qavatda, asosiy kirish yonida joylashgan. Tushlik vaqti 12:00-14:00.",
            "mood": "bottle",
        },
        "timetable": {
            "keywords": ["dars", "jadval", "schedule", "raspisaniye"],
            "reply": "Dars jadvalini aut.edupage.org/timetable sahifasida ko'rishingiz mumkin. Guruhingiz nomini ayting — men ham yordam beraman!",
            "mood": "studying",
        },
        "admission": {
            "keywords": ["qabul", "admission", "kirish", "hujjat"],
            "reply": "Qabul bo'limi 1-qavatda, 105-xonada. Hujjatlar haqida ma'lumot olish uchun admission@aut.uz ga yozing.",
            "mood": "explaining",
        },
        "wifi": {
            "keywords": ["wifi", "internet", "parol"],
            "reply": "AUT-WiFi tarmog'iga ulaning va talaba login/parolingizni kiriting. Muammo bo'lsa IT bo'limiga murojaat qiling.",
            "mood": "laptop",
        },
        "sport": {
            "keywords": ["sport", "futbol", "basketbol", "zalda"],
            "reply": "Sport zali asosiy bino orqasida joylashgan. Futbol va basketbol maydonchalari ham bor!",
            "mood": "soccer",
        },
        "exam": {
            "keywords": ["imtihon", "exam", "sessiya", "test"],
            "reply": "Imtihonlar har semestr oxirgi 2 haftada bo'lib o'tadi. Aniq sanalar uchun o'qituvchingizga murojaat qiling.",
            "mood": "working",
        },
        "lab": {
            "keywords": ["laboratoriya", "lab", "kompyuter", "computer"],
            "reply": "Kompyuter laboratoriyalari 4-qavatda, 401-405 xonalarda. Ular 8:00-20:00 gacha ochiq.",
            "mood": "laptop",
        },
        "contacts": {
            "keywords": ["telefon", "kontakt", "aloqa", "contact", "email"],
            "reply": "Qabul: +998 71 000 00 00\nQabul bo'limi: admission@aut.uz\nTalabalar ishlari: student@aut.uz",
            "mood": "explaining",
        },
        "programs": {
            "keywords": ["fakultet", "yo'nalish", "program", "mutaxassislik"],
            "reply": "AUT da 4 ta yo'nalish bor: Computer Science, Business Administration, Economics va Korean Studies.",
            "mood": "studying",
        },
        "parking": {
            "keywords": ["parking", "mashina", "avto"],
            "reply": "Avtoturargoh asosiy bino orqasida joylashgan. Talabalar uchun bepul!",
            "mood": "explaining",
        },
        "student_id": {
            "keywords": ["id", "guvohnoma", "talaba karta"],
            "reply": "Talaba guvohnomasini 1-qavatdagi 110-xona (Talabalar ishlari bo'limi) dan olishingiz mumkin.",
            "mood": "explaining",
        },
    },
    "ru": {
        "greeting": {
            "keywords": ["привет", "здравствуй", "салом", "хей", "добр"],
            "reply": "Привет! Я Чито — помощник AUT! Чем могу помочь?",
        },
        "rector": {
            "keywords": ["ректор", "rector"],
            "reply": "Кабинет ректора на 3 этаже, комната 301. Поднимитесь по главной лестнице и поверните направо.",
            "mood": "explaining",
        },
        "library": {
            "keywords": ["библиотек", "книг", "library"],
            "reply": "Библиотека на 2 этаже. Работает пн-пт с 9:00 до 18:00.",
            "mood": "studying",
        },
        "cafeteria": {
            "keywords": ["столов", "кафе", "обед", "еда", "кушать"],
            "reply": "Столовая на 1 этаже, рядом с главным входом. Обед с 12:00 до 14:00.",
            "mood": "bottle",
        },
        "timetable": {
            "keywords": ["расписан", "пары", "занят", "урок"],
            "reply": "Расписание можно посмотреть на aut.edupage.org/timetable. Скажите вашу группу — я помогу найти!",
            "mood": "studying",
        },
        "admission": {
            "keywords": ["поступ", "приём", "документ", "абитур"],
            "reply": "Приёмная комиссия на 1 этаже, каб. 105. По документам пишите на admission@aut.uz.",
            "mood": "explaining",
        },
        "wifi": {
            "keywords": ["wifi", "вай-фай", "интернет", "пароль"],
            "reply": "Подключитесь к AUT-WiFi и используйте логин/пароль студента. Проблемы? Обратитесь в IT-отдел.",
            "mood": "laptop",
        },
        "sport": {
            "keywords": ["спорт", "футбол", "баскетбол", "зал"],
            "reply": "Спортзал находится за главным зданием. Есть поля для футбола и баскетбола!",
            "mood": "soccer",
        },
        "exam": {
            "keywords": ["экзамен", "сессия", "тест", "зачёт"],
            "reply": "Экзамены проходят в последние 2 недели каждого семестра. Точные даты уточняйте у преподавателя.",
            "mood": "working",
        },
        "lab": {
            "keywords": ["лаборатор", "компьютер", "комп"],
            "reply": "Компьютерные лаборатории на 4 этаже, каб. 401-405. Открыты с 8:00 до 20:00.",
            "mood": "laptop",
        },
        "contacts": {
            "keywords": ["телефон", "контакт", "связь", "email", "почт"],
            "reply": "Ресепшн: +998 71 000 00 00\nПриёмная: admission@aut.uz\nСтуд. отдел: student@aut.uz",
            "mood": "explaining",
        },
        "programs": {
            "keywords": ["факультет", "направлен", "программ", "специальн"],
            "reply": "В AUT 4 направления: Computer Science, Business Administration, Economics и Korean Studies.",
            "mood": "studying",
        },
        "parking": {
            "keywords": ["парковк", "машин", "авто"],
            "reply": "Парковка за главным зданием. Для студентов бесплатно!",
            "mood": "explaining",
        },
        "student_id": {
            "keywords": ["студенческ", "удостоверен", "карт"],
            "reply": "Студенческое удостоверение выдаётся в каб. 110 (Отдел по работе со студентами), 1 этаж.",
            "mood": "explaining",
        },
    },
    "en": {
        "greeting": {
            "keywords": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "reply": "Hi! I'm Chito — your AUT assistant! How can I help you today?",
        },
        "rector": {
            "keywords": ["rector", "president", "director"],
            "reply": "The Rector's office is on the 3rd floor, Room 301. Take the main staircase and turn right.",
            "mood": "explaining",
        },
        "library": {
            "keywords": ["library", "book"],
            "reply": "The library is on the 2nd floor. Open Mon-Fri, 9:00-18:00.",
            "mood": "studying",
        },
        "cafeteria": {
            "keywords": ["cafeteria", "food", "lunch", "eat", "canteen"],
            "reply": "The cafeteria is on the 1st floor, next to the main entrance. Lunch hours: 12:00-14:00.",
            "mood": "bottle",
        },
        "timetable": {
            "keywords": ["timetable", "schedule", "class", "lesson"],
            "reply": "Check the timetable at aut.edupage.org/timetable. Tell me your group — I can help!",
            "mood": "studying",
        },
        "admission": {
            "keywords": ["admission", "apply", "document", "enroll"],
            "reply": "Admissions office is on the 1st floor, Room 105. Email: admission@aut.uz.",
            "mood": "explaining",
        },
        "wifi": {
            "keywords": ["wifi", "internet", "password", "connect"],
            "reply": "Connect to AUT-WiFi using your student credentials. Issues? Contact the IT department.",
            "mood": "laptop",
        },
        "sport": {
            "keywords": ["sport", "football", "soccer", "basketball", "gym"],
            "reply": "The gym is behind the main building. We have football and basketball courts!",
            "mood": "soccer",
        },
        "exam": {
            "keywords": ["exam", "test", "final", "midterm"],
            "reply": "Exams are held during the last 2 weeks of each semester. Check with your professor for exact dates.",
            "mood": "working",
        },
        "lab": {
            "keywords": ["lab", "computer"],
            "reply": "Computer labs are on the 4th floor, Rooms 401-405. Open 8:00-20:00.",
            "mood": "laptop",
        },
        "contacts": {
            "keywords": ["phone", "contact", "email", "call"],
            "reply": "Reception: +998 71 000 00 00\nAdmissions: admission@aut.uz\nStudent affairs: student@aut.uz",
            "mood": "explaining",
        },
        "programs": {
            "keywords": ["program", "major", "faculty", "department"],
            "reply": "AUT offers 4 programs: Computer Science, Business Administration, Economics, and Korean Studies.",
            "mood": "studying",
        },
        "parking": {
            "keywords": ["parking", "car"],
            "reply": "Parking is available behind the main building. Free for students!",
            "mood": "explaining",
        },
        "student_id": {
            "keywords": ["student id", "card", "badge"],
            "reply": "Student IDs are issued at Room 110 (Student Affairs), 1st floor.",
            "mood": "explaining",
        },
    },
    "kr": {
        "greeting": {
            "keywords": ["안녕", "하이", "헬로"],
            "reply": "안녕하세요! 저는 치토 — AUT 도우미예요! 무엇을 도와드릴까요?",
        },
        "rector": {
            "keywords": ["총장", "학장", "rector"],
            "reply": "총장실은 3층 301호에 있습니다. 중앙 계단으로 올라가서 오른쪽으로 가세요.",
            "mood": "explaining",
        },
        "library": {
            "keywords": ["도서관", "책", "library"],
            "reply": "도서관은 2층에 있습니다. 월-금 9:00-18:00 운영합니다.",
            "mood": "studying",
        },
        "cafeteria": {
            "keywords": ["식당", "밥", "점심", "cafeteria"],
            "reply": "식당은 1층 정문 옆에 있습니다. 점심시간: 12:00-14:00.",
            "mood": "bottle",
        },
        "timetable": {
            "keywords": ["시간표", "수업", "schedule"],
            "reply": "시간표는 aut.edupage.org/timetable에서 확인하세요. 학과를 알려주시면 도와드릴게요!",
            "mood": "studying",
        },
    },
}


def demo_response(message: str, locale: str) -> dict:
    """Provide demo responses using keyword matching."""
    msg_lower = message.lower()
    lang_data = DEMO_KEYWORDS.get(locale, DEMO_KEYWORDS["en"])

    for category in lang_data.values():
        for keyword in category["keywords"]:
            if keyword in msg_lower:
                mood = category.get("mood", "greeting")
                return {"reply": category["reply"], "mood": mood}

    defaults = {
        "uz": ("Kechirasiz, tushunmadim. Boshqacha so'rab ko'ring yoki quyidagi tugmalardan birini tanlang!", "thinking"),
        "ru": ("Извините, не совсем понял. Попробуйте спросить по-другому или выберите кнопку ниже!", "thinking"),
        "en": ("Sorry, I didn't quite understand. Try asking differently or use the buttons below!", "thinking"),
        "kr": ("죄송합니다, 이해하지 못했어요. 다르게 질문하거나 아래 버튼을 사용해주세요!", "thinking"),
    }
    reply, mood = defaults.get(locale, defaults["en"])
    return {"reply": reply, "mood": mood}
