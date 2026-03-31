from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.schemas import ChatRequest, ChatResponse
from ..models.db_models import Building
from ..database import get_db
from ..services.ai_service import chat

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    face_attrs = None
    if request.face_attributes:
        face_attrs = {
            "age": request.face_attributes.age,
            "gender": request.face_attributes.gender,
            "expression": request.face_attributes.expression,
            "lookalike": request.face_attributes.lookalike,
        }

    result = await chat(
        message=request.message,
        locale=request.locale,
        history=[{"role": m.role, "content": m.content} for m in request.history],
        user_name=request.user_name,
        face_attributes=face_attrs,
    )
    return ChatResponse(**result)


@router.get("/buildings")
async def get_buildings(db: AsyncSession = Depends(get_db)):
    """Public endpoint — campus buildings for map legend."""
    result = await db.execute(
        select(Building).where(Building.is_active == True).order_by(Building.num)
    )
    buildings = result.scalars().all()
    return [
        {"num": b.num, "name": b.name, "desc": b.description or "", "color": b.color}
        for b in buildings
    ]
