"""Admin router — CRUD for knowledge base, keywords, news; refresh endpoints."""

import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from pydantic import BaseModel

from ..database import get_db
from ..models.db_models import KnowledgeEntry, Keyword, NewsItem, InteractionLog, StaffMember, TimetableEntry, Building, Room
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


@router.post("/knowledge/reseed")
async def reseed_knowledge():
    """Delete all knowledge and re-seed from the latest AUT_KNOWLEDGE."""
    from ..services.seed_service import reseed_knowledge
    count = await reseed_knowledge()
    return {"status": "reseeded", "count": count}


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

    # Batch query: fetch all existing external_ids in one SELECT instead of N
    fetched_ext_ids = [item.get("external_id") for item in fetched if item.get("external_id")]
    existing_ext_ids: set[int] = set()
    if fetched_ext_ids:
        result = await db.execute(
            select(NewsItem.external_id).where(NewsItem.external_id.in_(fetched_ext_ids))
        )
        existing_ext_ids = {row[0] for row in result.fetchall()}

    added = 0
    for item in fetched:
        ext_id = item.get("external_id")
        if ext_id and ext_id in existing_ext_ids:
            continue
        news = NewsItem(
            external_id=ext_id,
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
    from ..services.staff_service import load_staff_cache
    await load_staff_cache()
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
    from ..services.staff_service import load_staff_cache
    await load_staff_cache()
    return member


@router.delete("/staff/{staff_id}", status_code=204)
async def delete_staff(staff_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StaffMember).where(StaffMember.id == staff_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Not found")
    await db.delete(member)
    await db.commit()
    from ..services.staff_service import load_staff_cache
    await load_staff_cache()


# ── Staff refresh ────────────────────────────────────────────────────────────

@router.post("/staff/refresh")
async def refresh_staff():
    """Re-parse staff data from ajou.uz and save to DB."""
    from ..services.staff_service import save_staff_to_db
    data = await asyncio.to_thread(_fetch_staff_data)
    staff_list = data.get("staff", [])
    saved = await save_staff_to_db(staff_list)
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
    """Re-parse timetable from aut.edupage.org and save to DB."""
    from ..services.timetable_service import _fetch_timetable_data, save_timetable_to_db
    data = await asyncio.to_thread(_fetch_timetable_data)
    if not data:
        raise HTTPException(500, "Failed to fetch timetable data")
    saved = await save_timetable_to_db(data)
    classes = len(data.get("schedule", {}))
    return {"classes": classes, "entries_saved": saved, "updated": data.get("updated")}


# ── Buildings CRUD ───────────────────────────────────────────────────────────

class BuildingIn(BaseModel):
    num: int
    name: str
    description: str | None = None
    photo: str | None = None
    color: str = "bg-blue-500"
    is_active: bool = True

class BuildingOut(BuildingIn):
    id: int
    class Config:
        from_attributes = True


@router.get("/buildings", response_model=list[BuildingOut])
async def list_buildings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Building).order_by(Building.num))
    return result.scalars().all()


@router.post("/buildings", response_model=BuildingOut, status_code=201)
async def create_building(data: BuildingIn, db: AsyncSession = Depends(get_db)):
    building = Building(**data.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    return building


@router.put("/buildings/{building_id}", response_model=BuildingOut)
async def update_building(building_id: int, data: BuildingIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    if not building:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(building, k, v)
    building.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(building)
    return building


@router.delete("/buildings/{building_id}", status_code=204)
async def delete_building(building_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Building).where(Building.id == building_id))
    building = result.scalar_one_or_none()
    if not building:
        raise HTTPException(404, "Not found")
    await db.delete(building)
    await db.commit()


# ── Rooms CRUD ────────────────────────────────────────────────────────────────

class RoomIn(BaseModel):
    name: str
    block: str | None = None
    floor: int | None = None
    capacity: int | None = None
    is_active: bool = True

class RoomOut(RoomIn):
    id: int
    class Config:
        from_attributes = True


@router.get("/rooms", response_model=list[RoomOut])
async def list_rooms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).order_by(Room.block, Room.name))
    return result.scalars().all()


@router.post("/rooms", response_model=RoomOut, status_code=201)
async def create_room(data: RoomIn, db: AsyncSession = Depends(get_db)):
    room = Room(**data.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.put("/rooms/{room_id}", response_model=RoomOut)
async def update_room(room_id: int, data: RoomIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(room, k, v)
    room.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(room)
    return room


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Room).where(Room.id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(404, "Not found")
    await db.delete(room)
    await db.commit()


@router.post("/rooms/sync")
async def sync_rooms_from_timetable(db: AsyncSession = Depends(get_db)):
    """Extract unique rooms from timetable entries and create Room records for any missing ones."""
    import re as _re

    # Get all unique room names from timetable
    tt_result = await db.execute(
        select(TimetableEntry.room).where(
            TimetableEntry.is_active == True,
            TimetableEntry.room != None,
            TimetableEntry.room != "",
        ).distinct()
    )
    tt_rooms = [row[0] for row in tt_result.fetchall()]

    # Get existing room names
    existing_result = await db.execute(select(Room.name))
    existing_names = {row[0] for row in existing_result.fetchall()}

    added = 0
    for room_name in tt_rooms:
        if room_name in existing_names:
            continue

        block = None
        floor = None

        # Patterns: "A-103", "A103", "A 103", "B-204", "C2-01", "C-2-01"
        # Block = letter prefix, Floor = first digit of number part
        m = _re.match(r'^([A-Za-z]+)[\s\-]*(\d)[\s\-]*(\d+)', room_name)
        if m:
            block = f"{m.group(1).upper()} Block"
            floor = int(m.group(2))
        else:
            # Try: "103A", "204B" — number first, letter suffix
            m2 = _re.match(r'^(\d)(\d{2,})[\s\-]*([A-Za-z]+)', room_name)
            if m2:
                floor = int(m2.group(1))
                block = f"{m2.group(3).upper()} Block"
            else:
                # Try just a number like "103" — floor from first digit
                m3 = _re.match(r'^(\d)(\d{2,})$', room_name.strip())
                if m3:
                    floor = int(m3.group(1))
                else:
                    # Named rooms with block prefix: "C-conf", "C-sport hall", "A-lab"
                    m4 = _re.match(r'^([A-Za-z])[\s\-]+(.+)', room_name)
                    if m4:
                        block = f"{m4.group(1).upper()} Block"

        db.add(Room(name=room_name, block=block, floor=floor))
        added += 1

    await db.commit()
    return {"synced": added, "total_timetable_rooms": len(tt_rooms), "existing": len(existing_names)}


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Return row counts for all tables and the current LLM mode."""
    from ..services.ai_service import get_llm_mode

    tables = {
        "knowledge": KnowledgeEntry,
        "keywords": Keyword,
        "news": NewsItem,
        "staff": StaffMember,
        "timetable": TimetableEntry,
        "buildings": Building,
        "rooms": Room,
        "logs": InteractionLog,
    }
    counts = {}
    for name, model in tables.items():
        result = await db.execute(select(func.count()).select_from(model))
        counts[name] = result.scalar()

    return {"counts": counts, "llm_mode": get_llm_mode()}


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
