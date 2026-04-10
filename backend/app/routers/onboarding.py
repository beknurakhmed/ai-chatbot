from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models.db_models import OnboardingTask, EmployeeOnboarding

router = APIRouter(prefix="/api", tags=["onboarding"])


@router.get("/onboarding/tasks")
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OnboardingTask)
        .where(OnboardingTask.is_active == True)
        .order_by(OnboardingTask.category, OnboardingTask.order_num)
    )
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "category": t.category,
            "order_num": t.order_num,
        }
        for t in tasks
    ]


@router.get("/onboarding/progress/{employee_name}")
async def get_progress(employee_name: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmployeeOnboarding).where(EmployeeOnboarding.employee_name == employee_name)
    )
    progress = result.scalars().all()
    completed_ids = {p.task_id for p in progress if p.is_completed}

    tasks_result = await db.execute(
        select(OnboardingTask)
        .where(OnboardingTask.is_active == True)
        .order_by(OnboardingTask.category, OnboardingTask.order_num)
    )
    tasks = tasks_result.scalars().all()

    return {
        "employee_name": employee_name,
        "total": len(tasks),
        "completed": len(completed_ids),
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "is_completed": t.id in completed_ids,
            }
            for t in tasks
        ],
    }


@router.post("/onboarding/complete")
async def complete_task(
    employee_name: str = Query(..., max_length=255),
    task_id: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployeeOnboarding).where(
            EmployeeOnboarding.employee_name == employee_name,
            EmployeeOnboarding.task_id == task_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.is_completed = True
        existing.completed_at = datetime.utcnow()
    else:
        record = EmployeeOnboarding(
            employee_name=employee_name,
            task_id=task_id,
            is_completed=True,
            completed_at=datetime.utcnow(),
        )
        db.add(record)

    await db.commit()
    return {"status": "completed", "employee_name": employee_name, "task_id": task_id}


@router.post("/onboarding/uncomplete")
async def uncomplete_task(
    employee_name: str = Query(..., max_length=255),
    task_id: int = Query(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EmployeeOnboarding).where(
            EmployeeOnboarding.employee_name == employee_name,
            EmployeeOnboarding.task_id == task_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.is_completed = False
        existing.completed_at = None
        await db.commit()

    return {"status": "uncompleted", "employee_name": employee_name, "task_id": task_id}
