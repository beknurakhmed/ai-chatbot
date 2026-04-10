from fastapi import APIRouter
from ..models.schemas import ChatRequest, ChatResponse
from ..services.ai_service import chat

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    result = await chat(
        message=request.message,
        locale=request.locale,
        history=[{"role": m.role, "content": m.content} for m in request.history],
        employee_name=request.employee_name,
    )
    return ChatResponse(**result)
