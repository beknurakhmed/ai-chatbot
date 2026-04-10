import re
from sqlalchemy import select, func, delete
from ..database import async_session
from ..models.db_models import KnowledgeEntry, Keyword, OnboardingTask, Department


def _parse_knowledge_sections() -> list[dict]:
    from .knowledge_base import UZUM_KNOWLEDGE

    entries = []
    sections = re.split(r'\n## ', UZUM_KNOWLEDGE)

    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().splitlines()
        title = lines[0].strip().lstrip('#').strip()
        content = '\n'.join(lines[1:]).strip()
        if not content:
            continue

        title_lower = title.lower()
        if any(w in title_lower for w in ['компани', 'структур', 'about']):
            category = 'company'
        elif any(w in title_lower for w in ['первый день', 'first day']):
            category = 'first_day'
        elif any(w in title_lower for w in ['инструмент', 'сервис', 'tools']):
            category = 'tools'
        elif any(w in title_lower for w in ['рабочий процесс', 'workflow']):
            category = 'workflow'
        elif any(w in title_lower for w in ['отпуск', 'больнич', 'vacation']):
            category = 'hr_policy'
        elif any(w in title_lower for w in ['бенефит', 'benefit']):
            category = 'benefits'
        elif any(w in title_lower for w in ['культур', 'culture']):
            category = 'culture'
        elif any(w in title_lower for w in ['безопасн', 'security']):
            category = 'security'
        elif any(w in title_lower for w in ['контакт', 'contact']):
            category = 'contacts'
        else:
            category = 'general'

        entries.append({
            'category': category,
            'title': title,
            'content': content,
            'language': 'ru',
        })

    return entries


SEED_KEYWORDS = [
    # Onboarding
    {"keyword": "онбординг", "intent": "onboarding", "language": "ru"},
    {"keyword": "адаптация", "intent": "onboarding", "language": "ru"},
    {"keyword": "чеклист", "intent": "onboarding", "language": "ru"},
    {"keyword": "план адаптации", "intent": "onboarding", "language": "ru"},
    {"keyword": "что делать", "intent": "onboarding", "language": "ru"},
    {"keyword": "первый день", "intent": "onboarding", "language": "ru"},
    {"keyword": "первая неделя", "intent": "onboarding", "language": "ru"},
    {"keyword": "с чего начать", "intent": "onboarding", "language": "ru"},
    {"keyword": "onboarding", "intent": "onboarding", "language": "en"},
    {"keyword": "checklist", "intent": "onboarding", "language": "en"},
    {"keyword": "first day", "intent": "onboarding", "language": "en"},
    {"keyword": "moslashtirish", "intent": "onboarding", "language": "uz"},
    {"keyword": "birinchi kun", "intent": "onboarding", "language": "uz"},

    # Tools
    {"keyword": "инструменты", "intent": "tools", "language": "ru"},
    {"keyword": "jira", "intent": "tools", "language": "all"},
    {"keyword": "gitlab", "intent": "tools", "language": "all"},
    {"keyword": "confluence", "intent": "tools", "language": "all"},
    {"keyword": "slack", "intent": "tools", "language": "all"},
    {"keyword": "vpn", "intent": "tools", "language": "all"},

    # HR
    {"keyword": "отпуск", "intent": "hr", "language": "ru"},
    {"keyword": "больничный", "intent": "hr", "language": "ru"},
    {"keyword": "зарплата", "intent": "hr", "language": "ru"},
    {"keyword": "бенефиты", "intent": "hr", "language": "ru"},
    {"keyword": "страховка", "intent": "hr", "language": "ru"},
    {"keyword": "vacation", "intent": "hr", "language": "en"},
    {"keyword": "benefits", "intent": "hr", "language": "en"},
    {"keyword": "ta'til", "intent": "hr", "language": "uz"},

    # Contacts
    {"keyword": "контакт", "intent": "contacts", "language": "ru"},
    {"keyword": "поддержка", "intent": "contacts", "language": "ru"},
    {"keyword": "помощь", "intent": "contacts", "language": "ru"},
    {"keyword": "hr", "intent": "contacts", "language": "all"},
    {"keyword": "it-support", "intent": "contacts", "language": "all"},
    {"keyword": "contact", "intent": "contacts", "language": "en"},
]


SEED_ONBOARDING_TASKS = [
    # Day 1
    {"title": "Получить рабочий ноутбук", "description": "Обратитесь в IT-отдел для получения оборудования", "category": "day_1", "order_num": 1},
    {"title": "Настроить корпоративную почту", "description": "Логин и пароль предоставит IT-отдел", "category": "day_1", "order_num": 2},
    {"title": "Установить Slack и войти", "description": "Основной мессенджер компании", "category": "day_1", "order_num": 3},
    {"title": "Пройти вводный тренинг с HR", "description": "Знакомство с компанией, политиками, бенефитами", "category": "day_1", "order_num": 4},
    {"title": "Познакомиться с наставником (buddy)", "description": "Ваш buddy поможет с любыми вопросами", "category": "day_1", "order_num": 5},

    # Week 1
    {"title": "Получить доступ к GitLab", "description": "gitlab.uzum.io — попросите тимлида добавить в проект", "category": "week_1", "order_num": 1},
    {"title": "Получить доступ к Jira", "description": "Трекер задач — тимлид добавит в нужный борд", "category": "week_1", "order_num": 2},
    {"title": "Изучить Confluence", "description": "Документация команды и проектов", "category": "week_1", "order_num": 3},
    {"title": "Настроить VPN", "description": "Для удалённого доступа к внутренним ресурсам", "category": "week_1", "order_num": 4},
    {"title": "Настроить dev-окружение", "description": "Клонировать репозиторий, настроить IDE, запустить проект локально", "category": "week_1", "order_num": 5},
    {"title": "Посетить первый daily standup", "description": "Каждый день в 10:00 — кратко расскажите чем занимаетесь", "category": "week_1", "order_num": 6},

    # Week 2
    {"title": "Выполнить первую задачу в Jira", "description": "Начните с небольшой задачи для знакомства с кодовой базой", "category": "week_2", "order_num": 1},
    {"title": "Пройти первый code review", "description": "Отправьте MR и получите обратную связь от команды", "category": "week_2", "order_num": 2},
    {"title": "Познакомиться с CI/CD", "description": "Узнайте как работает GitLab CI и ArgoCD", "category": "week_2", "order_num": 3},
    {"title": "Пройти тренинг по IT-безопасности", "description": "VPN, 2FA, правила работы с данными", "category": "week_2", "order_num": 4},

    # Month 1
    {"title": "Провести 1-on-1 с тимлидом", "description": "Обсудить цели на испытательный срок", "category": "month_1", "order_num": 1},
    {"title": "Изучить мониторинг (Grafana)", "description": "Дашборды вашего сервиса", "category": "month_1", "order_num": 2},
    {"title": "Самостоятельно взять задачу из спринта", "description": "Выберите задачу на sprint planning", "category": "month_1", "order_num": 3},
    {"title": "Заполнить первый pulse-опрос", "description": "Расскажите как проходит адаптация", "category": "month_1", "order_num": 4},
]


SEED_DEPARTMENTS = [
    {"name": "Backend", "description": "Серверная разработка, API, микросервисы", "head_name": None},
    {"name": "Frontend", "description": "Web-разработка, React, Next.js", "head_name": None},
    {"name": "Mobile", "description": "iOS и Android приложения", "head_name": None},
    {"name": "DevOps", "description": "Инфраструктура, CI/CD, Kubernetes", "head_name": None},
    {"name": "QA", "description": "Тестирование, автоматизация тестов", "head_name": None},
    {"name": "Data", "description": "Аналитика, ML, Data Engineering", "head_name": None},
    {"name": "Product", "description": "Продуктовый менеджмент", "head_name": None},
    {"name": "Design", "description": "UX/UI дизайн", "head_name": None},
]


async def reseed_knowledge() -> int:
    async with async_session() as db:
        await db.execute(delete(KnowledgeEntry))
        entries = _parse_knowledge_sections()
        for e in entries:
            db.add(KnowledgeEntry(**e))
        await db.commit()
    from .knowledge_db_service import refresh
    await refresh()
    return len(entries)


async def seed_if_empty() -> dict:
    counts = {"knowledge": 0, "keywords": 0, "onboarding_tasks": 0, "departments": 0}

    async with async_session() as db:
        # Knowledge
        kb_count = await db.scalar(select(func.count()).select_from(KnowledgeEntry))
        if kb_count == 0:
            entries = _parse_knowledge_sections()
            for e in entries:
                db.add(KnowledgeEntry(**e))
            counts["knowledge"] = len(entries)

        # Keywords
        kw_count = await db.scalar(select(func.count()).select_from(Keyword))
        if kw_count == 0:
            for kw in SEED_KEYWORDS:
                db.add(Keyword(**kw))
            counts["keywords"] = len(SEED_KEYWORDS)

        # Onboarding tasks
        task_count = await db.scalar(select(func.count()).select_from(OnboardingTask))
        if task_count == 0:
            for t in SEED_ONBOARDING_TASKS:
                db.add(OnboardingTask(**t))
            counts["onboarding_tasks"] = len(SEED_ONBOARDING_TASKS)

        # Departments
        dept_count = await db.scalar(select(func.count()).select_from(Department))
        if dept_count == 0:
            for d in SEED_DEPARTMENTS:
                db.add(Department(**d))
            counts["departments"] = len(SEED_DEPARTMENTS)

        await db.commit()

    if any(counts.values()):
        print(f"[Seed] Inserted: {counts}")
    else:
        print("[Seed] DB already populated, skipping.")

    return counts
