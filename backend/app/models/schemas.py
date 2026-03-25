from pydantic import BaseModel


class MessageItem(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class FaceAttributesInput(BaseModel):
    age: int | None = None
    gender: str | None = None
    expression: str | None = None
    expressionScore: float = 0
    lookalike: str | None = None


class ChatRequest(BaseModel):
    message: str
    locale: str = "uz"
    history: list[MessageItem] = []
    user_name: str | None = None
    face_attributes: FaceAttributesInput | None = None


class TimetableLesson(BaseModel):
    day: str
    period: str
    time: str
    subject: str
    teacher: str
    room: str


class TimetableData(BaseModel):
    group: str
    lessons: list[TimetableLesson]


class StaffMember(BaseModel):
    name: str
    position: str
    photo: str = ""


class ChatResponse(BaseModel):
    reply: str
    mood: str = "explaining"
    timetable: TimetableData | None = None
    staff: list[StaffMember] | None = None
    map: bool = False


class FaceRecognizeRequest(BaseModel):
    image: str  # base64 encoded image


class FaceRecognizeResponse(BaseModel):
    name: str | None = None
    confidence: float = 0.0
