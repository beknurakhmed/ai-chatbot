from fastapi import APIRouter
from ..models.schemas import ChatRequest, ChatResponse
from ..services.ai_service import chat

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
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
