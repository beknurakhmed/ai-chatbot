import json
from pathlib import Path
from fastapi import APIRouter
from ..models.schemas import FaceRecognizeRequest, FaceRecognizeResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/face", tags=["face"])

FACES_DIR = Path(__file__).parent.parent / "data" / "faces"
FACES_DIR.mkdir(parents=True, exist_ok=True)


class FaceSaveRequest(BaseModel):
    name: str
    descriptor: list[float]


class FaceSaveResponse(BaseModel):
    ok: bool


class KnownFace(BaseModel):
    name: str
    descriptor: list[float]


class FaceListResponse(BaseModel):
    faces: list[KnownFace]


@router.get("/list", response_model=FaceListResponse)
async def list_faces():
    """Return all saved face descriptors."""
    faces = []
    for f in FACES_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            faces.append(KnownFace(name=data["name"], descriptor=data["descriptor"]))
        except Exception:
            continue
    return FaceListResponse(faces=faces)


@router.post("/save", response_model=FaceSaveResponse)
async def save_face(req: FaceSaveRequest):
    """Save a face descriptor to disk."""
    # Use name as filename (sanitized)
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in req.name).strip()
    if not safe_name:
        return FaceSaveResponse(ok=False)

    filepath = FACES_DIR / f"{safe_name}.json"
    filepath.write_text(
        json.dumps({"name": req.name, "descriptor": req.descriptor}, ensure_ascii=False),
        encoding="utf-8",
    )
    return FaceSaveResponse(ok=True)
