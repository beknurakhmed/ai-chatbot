"""Knowledge DB service — loads knowledge entries and keywords from database.

Maintains an in-memory cache, refreshed on startup and via admin /refresh endpoint.
Falls back to static knowledge_base.py if DB has no entries.
"""

import asyncio
from sqlalchemy import select
from ..database import async_session
from ..models.db_models import KnowledgeEntry, Keyword

# ── In-memory cache ──────────────────────────────────────────────────────────

_knowledge_text: str = ""
_keywords_by_intent: dict[str, list[str]] = {}
_loaded: bool = False


async def _load_from_db() -> None:
    global _knowledge_text, _keywords_by_intent, _loaded

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


async def refresh() -> None:
    """Reload knowledge and keywords from DB. Call after admin changes."""
    await _load_from_db()


async def get_knowledge_text() -> str:
    """Return combined knowledge text from DB (or static fallback)."""
    if not _loaded:
        await _load_from_db()

    if _knowledge_text:
        return _knowledge_text

    # Fallback to static knowledge base
    from .knowledge_base import get_knowledge
    return get_knowledge()


async def get_keywords_by_intent(intent: str) -> list[str]:
    """Return keywords for a specific intent from DB."""
    if not _loaded:
        await _load_from_db()
    return _keywords_by_intent.get(intent, [])


async def get_all_keywords() -> dict[str, list[str]]:
    """Return all keywords grouped by intent."""
    if not _loaded:
        await _load_from_db()
    return dict(_keywords_by_intent)
