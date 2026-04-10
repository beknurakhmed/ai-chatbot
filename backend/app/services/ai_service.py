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
}

SYSTEM_PROMPT_TEMPLATE = """You are Uzumchi, a friendly assistant for new IT employees at Uzum — the largest tech ecosystem in Uzbekistan.

CRITICAL LANGUAGE RULE: {lang_instruction}

Your role:
- Help new employees with onboarding questions
- Explain company processes, tools, and culture
- Guide through the first days, weeks, and months
- Be supportive, friendly, and encouraging
- Keep answers brief (2-4 sentences max) and practical

Use ONLY the knowledge base below to answer. If unsure, suggest contacting HR or IT support.

End your response with [mood:NAME] on a new line.
Moods: greeting, explaining, thinking, happy, sad, warning, celebrating, curious, waving, presenting

Knowledge:
{knowledge}
"""

LANG_NAMES = {"en": "English", "uz": "Uzbek", "ru": "Russian"}


async def translate_tasks(tasks: list[dict], locale: str) -> list[dict]:
    if locale == "ru" or not tasks:
        return tasks

    lang = LANG_NAMES.get(locale, "English")
    lines = []
    for i, t in enumerate(tasks):
        lines.append(f"{i}|{t['title']}|{t.get('description') or ''}")
    block = "\n".join(lines)

    prompt = (
        f"Translate each line to {lang}. Keep the format: NUMBER|TITLE|DESCRIPTION. "
        f"Do NOT add anything else. Do NOT change numbers. Keep technical terms (GitLab, Jira, Slack, VPN, CI/CD, etc) as is.\n\n{block}"
    )

    try:
        import ollama as ollama_lib
        model = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        ollama_client = ollama_lib.AsyncClient(host=host)
        response = await ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            keep_alive=-1,
        )
        result_text = response["message"]["content"].strip()

        translated = {}
        for line in result_text.splitlines():
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|", 2)
            if len(parts) >= 2:
                try:
                    idx = int(parts[0].strip())
                    translated[idx] = {
                        "title": parts[1].strip(),
                        "description": parts[2].strip() if len(parts) > 2 and parts[2].strip() else None,
                    }
                except ValueError:
                    continue

        result = []
        for i, t in enumerate(tasks):
            if i in translated:
                result.append({**t, "title": translated[i]["title"], "description": translated[i]["description"] or t.get("description")})
            else:
                result.append(t)
        return result
    except Exception:
        return tasks


VALID_MOODS = {
    "greeting", "explaining", "thinking", "happy", "sad", "warning",
    "celebrating", "curious", "waving", "presenting", "idle",
    "talking", "smiling", "winking",
}


def get_llm_mode() -> str:
    if os.environ.get("OLLAMA_MODEL"):
        return "ollama"
    if os.environ.get("LOCAL_LLM_URL"):
        return "local"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return "ollama"


def get_client() -> AsyncAnthropic:
    global client
    if client is None:
        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    return client


def clean_response(text: str) -> str:
    text = re.sub(r"<\|im_start\|>.*?(?:<\|im_end\|>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<\|.*?\|>", "", text)
    text = re.sub(r"<s>|</s>", "", text)
    return text.strip()


async def build_system_prompt(locale: str, employee_name: str | None = None) -> str:
    lang_instruction = LOCALE_INSTRUCTIONS.get(locale, LOCALE_INSTRUCTIONS["ru"])
    knowledge = await get_knowledge_text()
    prompt = SYSTEM_PROMPT_TEMPLATE.format(lang_instruction=lang_instruction, knowledge=knowledge)
    if employee_name:
        prompt += f"\n\nThe employee's name is: {employee_name}. Address them by name warmly."
    return prompt


def extract_mood(text: str) -> tuple[str, str]:
    text = clean_response(text)
    match = re.search(r"\[mood:(\w+)\]", text)
    if match:
        mood = match.group(1)
        clean = text[:match.start()].strip()
        if mood in VALID_MOODS:
            return clean, mood
        return clean, "explaining"
    return text.strip(), "explaining"


async def chat(message: str, locale: str = "ru", history: list[dict] | None = None, employee_name: str | None = None) -> dict:
    hist = history or []
    msg_lower = message.lower()

    onboarding_kws = await get_keywords_by_intent("onboarding")
    is_onboarding = any(kw in msg_lower for kw in onboarding_kws)

    if is_onboarding:
        from ..database import async_session
        from ..models.db_models import OnboardingTask
        from sqlalchemy import select

        try:
            async with async_session() as db:
                result = await db.execute(
                    select(OnboardingTask)
                    .where(OnboardingTask.is_active == True)
                    .order_by(OnboardingTask.category, OnboardingTask.order_num)
                )
                tasks = result.scalars().all()
                task_list = [
                    {"id": t.id, "title": t.title, "description": t.description, "category": t.category}
                    for t in tasks
                ]
                task_list = await translate_tasks(task_list, locale)
        except Exception:
            task_list = []

        header = {
            "ru": "Вот ваш план адаптации в Uzum:",
            "uz": "Uzum-ga moslashish rejangiz:",
            "en": "Here's your onboarding plan at Uzum:",
        }
        return {
            "reply": header.get(locale, header["ru"]),
            "mood": "presenting",
            "onboarding": task_list,
        }

    mode = get_llm_mode()

    if mode == "ollama":
        result = await chat_ollama(message, locale, hist, employee_name)
    elif mode == "local":
        result = await chat_local(message, locale, hist, employee_name)
    elif mode == "claude":
        result = await chat_claude(message, locale, hist, employee_name)
    else:
        result = demo_response(message, locale)

    return result


async def chat_claude(message: str, locale: str, history: list[dict], employee_name: str | None = None) -> dict:
    anthropic = get_client()
    system_prompt = await build_system_prompt(locale, employee_name)

    messages = []
    for msg in history[-10:]:
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


async def chat_local(message: str, locale: str, history: list[dict], employee_name: str | None = None) -> dict:
    base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:1234")
    model = os.environ.get("LOCAL_LLM_MODEL", "local-model")
    system_prompt = await build_system_prompt(locale, employee_name)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(
                f"{base_url}/v1/chat/completions",
                json={"model": model, "messages": messages, "max_tokens": 1024, "temperature": 0.7},
            )
        if response.status_code != 200:
            return demo_response(message, locale)
        data = response.json()
        text = data["choices"][0]["message"]["content"]
        reply, mood = extract_mood(text)
        return {"reply": reply, "mood": mood}
    except Exception:
        return demo_response(message, locale)


async def chat_ollama(message: str, locale: str, history: list[dict], employee_name: str | None = None) -> dict:
    import ollama as ollama_lib

    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    system_prompt = await build_system_prompt(locale, employee_name)

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    try:
        ollama_client = ollama_lib.AsyncClient(host=host)
        response = await ollama_client.chat(model=model, messages=messages, keep_alive=-1)
        text = response["message"]["content"]
        reply, mood = extract_mood(text)
        return {"reply": reply, "mood": mood}
    except Exception:
        return demo_response(message, locale)


def demo_response(message: str, locale: str) -> dict:
    defaults = {
        "uz": "Kechirasiz, hozir javob bera olmayman. Iltimos, keyinroq urinib ko'ring.",
        "ru": "Извините, сейчас не могу ответить. Пожалуйста, попробуйте позже.",
        "en": "Sorry, I can't respond right now. Please try again later.",
    }
    return {"reply": defaults.get(locale, defaults["ru"]), "mood": "sad"}
