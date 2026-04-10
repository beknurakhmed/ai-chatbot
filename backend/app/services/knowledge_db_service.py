import asyncio
import time
from sqlalchemy import select
from ..database import async_session
from ..models.db_models import KnowledgeEntry, Keyword

_knowledge_text: str = ""
_keywords_by_intent: dict[str, list[str]] = {}
_loaded: bool = False
_last_loaded: float = 0.0
_CACHE_TTL: float = 300.0  # 5 minutes


def _cache_expired() -> bool:
    return (time.monotonic() - _last_loaded) > _CACHE_TTL


async def _load_from_db() -> None:
    global _knowledge_text, _keywords_by_intent, _loaded, _last_loaded

    async with async_session() as db:
        # Load active knowledge entries
        result = await db.execute(
            select(KnowledgeEntry)
            .where(KnowledgeEntry.is_active == True)
            .order_by(KnowledgeEntry.category, KnowledgeEntry.id)
        )
        entries = result.scalars().all()

        if entries:
            parts = []
            current_category = None
            for e in entries:
                if e.category != current_category:
                    parts.append(f"\n## {e.category.title()}")
                    current_category = e.category
                parts.append(f"### {e.title}\n{e.content}")
            _knowledge_text = "\n".join(parts)
        else:
            _knowledge_text = ""

        # Load active keywords
        kw_result = await db.execute(
            select(Keyword).where(Keyword.is_active == True)
        )
        keywords = kw_result.scalars().all()

        by_intent: dict[str, list[str]] = {}
        for kw in keywords:
            by_intent.setdefault(kw.intent, []).append(kw.keyword.lower())
        _keywords_by_intent = by_intent

    _loaded = True
    _last_loaded = time.monotonic()


async def refresh() -> None:
    await _load_from_db()


async def get_knowledge_text() -> str:
    if not _loaded or _cache_expired():
        await _load_from_db()

    return _knowledge_text


async def get_keywords_by_intent(intent: str) -> list[str]:
    if not _loaded or _cache_expired():
        await _load_from_db()
    return _keywords_by_intent.get(intent, [])


async def get_all_keywords() -> dict[str, list[str]]:
    if not _loaded:
        await _load_from_db()
    return dict(_keywords_by_intent)
