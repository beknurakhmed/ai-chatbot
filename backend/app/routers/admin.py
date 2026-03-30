"""Admin router — CRUD for knowledge base, keywords, news; refresh endpoints."""

import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel

from ..database import get_db
from ..models.db_models import KnowledgeEntry, Keyword, NewsItem, InteractionLog, StaffMember, TimetableEntry
from ..services.news_service import fetch_news_async
from ..services.staff_service import _fetch_staff_data
import asyncio

_bearer = HTTPBearer()

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "chito-admin-secret")


def require_admin(creds: HTTPAuthorizationCredentials = Security(_bearer)):
    if creds.credentials != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ── Pydantic schemas ────────────────────────────────────────────────────────

class KnowledgeIn(BaseModel):
    category: str
    title: str
    content: str
    language: str = "en"
    is_active: bool = True

class KnowledgeOut(KnowledgeIn):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class KeywordIn(BaseModel):
    keyword: str
    intent: str
    language: str = "all"
    is_active: bool = True

class KeywordOut(KeywordIn):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class NewsOut(BaseModel):
    id: int
    external_id: int | None
    title: str
    content: str | None
    url: str | None
    image_url: str | None
    published_at: datetime | None
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class NewsIn(BaseModel):
    external_id: int | None = None
    title: str
    content: str | None = None
    url: str | None = None
    image_url: str | None = None
    published_at: datetime | None = None
    is_active: bool = True


# ── Knowledge Base ──────────────────────────────────────────────────────────

@router.get("/knowledge", response_model=list[KnowledgeOut])
async def list_knowledge(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).order_by(KnowledgeEntry.category, KnowledgeEntry.id))
    return result.scalars().all()


@router.post("/knowledge", response_model=KnowledgeOut, status_code=201)
async def create_knowledge(data: KnowledgeIn, db: AsyncSession = Depends(get_db)):
    entry = KnowledgeEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.put("/knowledge/{entry_id}", response_model=KnowledgeOut)
async def update_knowledge(entry_id: int, data: KnowledgeIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(entry, k, v)
    entry.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/knowledge/{entry_id}", status_code=204)
async def delete_knowledge(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Not found")
    await db.delete(entry)
    await db.commit()


@router.post("/knowledge/refresh-cache")
async def refresh_knowledge_cache():
    """Reload knowledge + keywords cache from DB (call after bulk changes)."""
    from ..services.knowledge_db_service import refresh
    await refresh()
    return {"status": "refreshed"}


# ── Keywords ────────────────────────────────────────────────────────────────

@router.get("/keywords", response_model=list[KeywordOut])
async def list_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).order_by(Keyword.intent, Keyword.keyword))
    return result.scalars().all()


@router.post("/keywords", response_model=KeywordOut, status_code=201)
async def create_keyword(data: KeywordIn, db: AsyncSession = Depends(get_db)):
    kw = Keyword(**data.model_dump())
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return kw


@router.put("/keywords/{kw_id}", response_model=KeywordOut)
async def update_keyword(kw_id: int, data: KeywordIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).where(Keyword.id == kw_id))
    kw = result.scalar_one_or_none()
    if not kw:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(kw, k, v)
    await db.commit()
    await db.refresh(kw)
    return kw


@router.delete("/keywords/{kw_id}", status_code=204)
async def delete_keyword(kw_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).where(Keyword.id == kw_id))
    kw = result.scalar_one_or_none()
    if not kw:
        raise HTTPException(404, "Not found")
    await db.delete(kw)
    await db.commit()


# ── News ────────────────────────────────────────────────────────────────────

@router.get("/news", response_model=list[NewsOut])
async def list_news(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsItem).order_by(NewsItem.published_at.desc().nullslast(), NewsItem.id.desc()))
    return result.scalars().all()


@router.post("/news", response_model=NewsOut, status_code=201)
async def create_news(data: NewsIn, db: AsyncSession = Depends(get_db)):
    item = NewsItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/news/{news_id}", response_model=NewsOut)
async def update_news(news_id: int, data: NewsIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsItem).where(NewsItem.id == news_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/news/{news_id}", status_code=204)
async def delete_news(news_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NewsItem).where(NewsItem.id == news_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Not found")
    await db.delete(item)
    await db.commit()


@router.post("/news/refresh")
async def refresh_news(db: AsyncSession = Depends(get_db)):
    """Fetch latest news from ajou.uz and save new items to DB."""
    fetched = await fetch_news_async(limit=30)
    added = 0
    for item in fetched:
        ext_id = item.get("external_id")
        if ext_id:
            existing = await db.execute(select(NewsItem).where(NewsItem.external_id == ext_id))
            if existing.scalar_one_or_none():
                continue
        news = NewsItem(
            external_id=item.get("external_id"),
            title=item["title"],
            content=item.get("content", ""),
            url=item.get("url"),
            image_url=item.get("image_url"),
            published_at=item.get("published_at"),
        )
        db.add(news)
        added += 1
    await db.commit()
    return {"added": added, "fetched": len(fetched)}


# ── Staff CRUD ───────────────────────────────────────────────────────────────

class StaffIn(BaseModel):
    name: str
    position: str | None = None
    photo: str | None = None
    category: str | None = None
    is_active: bool = True

class StaffOut(StaffIn):
    id: int
    class Config:
        from_attributes = True


@router.get("/staff", response_model=list[StaffOut])
async def list_staff(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffMember).order_by(StaffMember.category, StaffMember.name))
    return result.scalars().all()


@router.post("/staff", response_model=StaffOut, status_code=201)
async def create_staff(data: StaffIn, db: AsyncSession = Depends(get_db)):
    member = StaffMember(**data.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.put("/staff/{staff_id}", response_model=StaffOut)
async def update_staff(staff_id: int, data: StaffIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffMember).where(StaffMember.id == staff_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(member, k, v)
    member.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/staff/{staff_id}", status_code=204)
async def delete_staff(staff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffMember).where(StaffMember.id == staff_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Not found")
    await db.delete(member)
    await db.commit()


# ── Staff refresh ────────────────────────────────────────────────────────────

@router.post("/staff/refresh")
async def refresh_staff():
    """Re-parse staff data from ajou.uz, save to DB and update cache file."""
    import json
    from pathlib import Path
    from ..services.staff_service import save_staff_to_db
    data = await asyncio.to_thread(_fetch_staff_data)
    staff_list = data.get("staff", [])
    # Save to DB
    saved = await save_staff_to_db(staff_list)
    # Also update JSON cache as backup
    cache_file = Path(__file__).parent.parent / "data" / "staff_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"count": saved, "updated": data.get("updated")}


# ── Timetable CRUD ───────────────────────────────────────────────────────────

class TimetableIn(BaseModel):
    group: str
    day: str
    period: str
    time_str: str
    subject: str
    teacher: str | None = None
    room: str | None = None
    is_active: bool = True

class TimetableOut(TimetableIn):
    id: int
    class Config:
        from_attributes = True


@router.get("/timetable", response_model=list[TimetableOut])
async def list_timetable(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TimetableEntry).order_by(TimetableEntry.group, TimetableEntry.day, TimetableEntry.period))
    return result.scalars().all()


@router.post("/timetable", response_model=TimetableOut, status_code=201)
async def create_timetable(data: TimetableIn, db: AsyncSession = Depends(get_db)):
    entry = TimetableEntry(**data.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.put("/timetable/{entry_id}", response_model=TimetableOut)
async def update_timetable(entry_id: int, data: TimetableIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TimetableEntry).where(TimetableEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(entry, k, v)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/timetable/{entry_id}", status_code=204)
async def delete_timetable(entry_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TimetableEntry).where(TimetableEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Not found")
    await db.delete(entry)
    await db.commit()


# ── Timetable refresh ────────────────────────────────────────────────────────

@router.post("/timetable/refresh")
async def refresh_timetable():
    """Re-parse timetable from aut.edupage.org, save to DB and update cache."""
    import json
    from ..services.timetable_service import _fetch_timetable_data, CACHE_FILE, save_timetable_to_db
    data = await asyncio.to_thread(_fetch_timetable_data)
    if not data:
        raise HTTPException(500, "Failed to fetch timetable data")
    # Save to DB
    saved = await save_timetable_to_db(data)
    # Also update JSON cache as backup
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    classes = len(data.get("schedule", {}))
    return {"classes": classes, "entries_saved": saved, "updated": data.get("updated")}


# ── Logs ─────────────────────────────────────────────────────────────────────

@router.get("/logs")
async def list_logs(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InteractionLog).order_by(InteractionLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "user_name": l.user_name,
            "message": l.message,
            "reply": l.reply,
            "locale": l.locale,
            "mood": l.mood,
            "created_at": l.created_at,
        }
        for l in logs
    ]
