from datetime import date
from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models.db_models import PulseSurvey
from ..models.schemas import PulseSurveyIn

router = APIRouter(prefix="/api", tags=["survey"])


@router.post("/survey")
async def submit_survey(data: PulseSurveyIn, db: AsyncSession = Depends(get_db)):
    survey = PulseSurvey(
        employee_name=data.employee_name,
        mood_score=data.mood_score,
        comment=data.comment,
        category=data.category,
        survey_date=data.survey_date,
    )
    db.add(survey)
    await db.commit()
    await db.refresh(survey)
    return {"id": survey.id, "status": "submitted"}


@router.get("/survey/{employee_name}")
async def get_surveys(employee_name: str = Path(..., max_length=255), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PulseSurvey)
        .where(PulseSurvey.employee_name == employee_name)
        .order_by(PulseSurvey.survey_date.desc())
        .limit(30)
    )
    surveys = result.scalars().all()
    return [
        {
            "id": s.id,
            "mood_score": s.mood_score,
            "comment": s.comment,
            "category": s.category,
            "survey_date": s.survey_date.isoformat(),
        }
        for s in surveys
    ]


@router.get("/survey/stats/summary")
async def get_survey_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            PulseSurvey.employee_name,
            func.avg(PulseSurvey.mood_score).label("avg_mood"),
            func.count(PulseSurvey.id).label("total_surveys"),
        )
        .group_by(PulseSurvey.employee_name)
    )
    rows = result.fetchall()
    return [
        {
            "employee_name": r.employee_name,
            "avg_mood": round(float(r.avg_mood), 1),
            "total_surveys": r.total_surveys,
        }
        for r in rows
    ]
