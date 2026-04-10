from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class MessageItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=10000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    locale: str = Field(default="ru", pattern=r"^(ru|uz|en)$")
    history: list[MessageItem] = Field(default=[], max_length=50)
    employee_name: str | None = Field(default=None, max_length=255)


class ChatResponse(BaseModel):
    reply: str
    mood: str = "explaining"
    onboarding: list[dict] | None = None


class OnboardingTaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    category: str
    order_num: int
    is_completed: bool = False

    class Config:
        from_attributes = True


class PulseSurveyIn(BaseModel):
    employee_name: str = Field(..., min_length=1, max_length=255)
    mood_score: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    category: str = Field(default="general", max_length=100)
    survey_date: date


class PulseSurveyOut(PulseSurveyIn):
    id: int

    class Config:
        from_attributes = True
