import hmac
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.db_models import (
    KnowledgeEntry, Keyword, InteractionLog,
    OnboardingTask, EmployeeOnboarding, PulseSurvey, Department,
)

_bearer = HTTPBearer()

ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")
if not ADMIN_TOKEN:
    raise RuntimeError("ADMIN_TOKEN environment variable is required")


def require_admin(creds: HTTPAuthorizationCredentials = Security(_bearer)):
    if not hmac.compare_digest(creds.credentials, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid admin token")


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class KnowledgeIn(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1, max_length=50000)
    language: str = Field(default="ru", max_length=10)
    is_active: bool = True

class KnowledgeOut(KnowledgeIn):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class KeywordIn(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    intent: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="all", max_length=10)
    is_active: bool = True

class KeywordOut(KeywordIn):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class OnboardingTaskIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    category: str = Field(..., min_length=1, max_length=100)
    order_num: int = Field(default=0, ge=0)
    is_active: bool = True

class OnboardingTaskOut(OnboardingTaskIn):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class DepartmentIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    head_name: str | None = Field(default=None, max_length=255)
    is_active: bool = True

class DepartmentOut(DepartmentIn):
    id: int
    class Config:
        from_attributes = True


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
    from ..services.knowledge_db_service import refresh
    await refresh()
    return {"status": "refreshed"}

@router.post("/knowledge/reseed")
async def reseed_knowledge():
    from ..services.seed_service import reseed_knowledge
    count = await reseed_knowledge()
    return {"status": "reseeded", "count": count}


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


@router.get("/onboarding-tasks", response_model=list[OnboardingTaskOut])
async def list_onboarding_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OnboardingTask).order_by(OnboardingTask.category, OnboardingTask.order_num))
    return result.scalars().all()

@router.post("/onboarding-tasks", response_model=OnboardingTaskOut, status_code=201)
async def create_onboarding_task(data: OnboardingTaskIn, db: AsyncSession = Depends(get_db)):
    task = OnboardingTask(**data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.put("/onboarding-tasks/{task_id}", response_model=OnboardingTaskOut)
async def update_onboarding_task(task_id: int, data: OnboardingTaskIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OnboardingTask).where(OnboardingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(task, k, v)
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/onboarding-tasks/{task_id}", status_code=204)
async def delete_onboarding_task(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OnboardingTask).where(OnboardingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Not found")
    await db.delete(task)
    await db.commit()


@router.get("/departments", response_model=list[DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).order_by(Department.name))
    return result.scalars().all()

@router.post("/departments", response_model=DepartmentOut, status_code=201)
async def create_department(data: DepartmentIn, db: AsyncSession = Depends(get_db)):
    dept = Department(**data.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

@router.put("/departments/{dept_id}", response_model=DepartmentOut)
async def update_department(dept_id: int, data: DepartmentIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items():
        setattr(dept, k, v)
    await db.commit()
    await db.refresh(dept)
    return dept

@router.delete("/departments/{dept_id}", status_code=204)
async def delete_department(dept_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(404, "Not found")
    await db.delete(dept)
    await db.commit()


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    from ..services.ai_service import get_llm_mode

    tables = {
        "knowledge": KnowledgeEntry,
        "keywords": Keyword,
        "onboarding_tasks": OnboardingTask,
        "departments": Department,
        "employee_progress": EmployeeOnboarding,
        "surveys": PulseSurvey,
        "logs": InteractionLog,
    }
    counts = {}
    for name, model in tables.items():
        result = await db.execute(select(func.count()).select_from(model))
        counts[name] = result.scalar()

    # Survey avg mood
    avg_result = await db.execute(select(func.avg(PulseSurvey.mood_score)))
    avg_mood = avg_result.scalar()

    return {
        "counts": counts,
        "llm_mode": get_llm_mode(),
        "avg_mood": round(float(avg_mood), 1) if avg_mood else None,
    }


@router.get("/logs")
async def list_logs(limit: int = Query(default=100, ge=1, le=1000), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InteractionLog).order_by(InteractionLog.created_at.desc()).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "employee_name": l.employee_name,
            "message": l.message,
            "reply": l.reply,
            "locale": l.locale,
            "mood": l.mood,
            "created_at": l.created_at,
        }
        for l in logs
    ]
