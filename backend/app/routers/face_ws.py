"""
WebSocket endpoint for real-time face analysis.
Uses InsightFace for detection + PostgreSQL/pgvector for recognition.
"""

import base64
import json
import asyncio
import numpy as np
import cv2
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.face_service import get_face_app, detect_expression
from ..services.face_db_service import recognize_face, find_lookalike, save_face

router = APIRouter()


def decode_frame(data: str) -> np.ndarray | None:
    try:
        if "," in data:
            data = data.split(",", 1)[1]
        img_bytes = base64.b64decode(data)
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def analyze_face_sync(img_bgr: np.ndarray) -> dict:
    """Run InsightFace detection (sync part)."""
    app = get_face_app()
    faces = app.get(img_bgr)
    if not faces:
        return {"detected": False}

    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

    bbox = face.bbox.astype(int).tolist()
    age = int(face.age) if hasattr(face, "age") else None
    gender = "M" if getattr(face, "gender", None) == 1 else "F" if getattr(face, "gender", None) == 0 else None
    expression = detect_expression(face)
    embedding = face.embedding.tolist() if hasattr(face, "embedding") and face.embedding is not None else None

    return {
        "detected": True,
        "age": age,
        "gender": gender,
        "expression": expression,
        "bbox": bbox,
        "embedding": embedding,
    }


@router.websocket("/ws/face")
async def face_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action", "analyze")

            if action == "analyze":
                frame_data = msg.get("frame")
                if not frame_data:
                    await websocket.send_json({"error": "no frame"})
                    continue

                img = decode_frame(frame_data)
                if img is None:
                    await websocket.send_json({"error": "decode failed"})
                    continue

                # Run InsightFace in thread (CPU-bound)
                result = await asyncio.to_thread(analyze_face_sync, img)

                if not result["detected"]:
                    await websocket.send_json({"detected": False})
                    continue

                # DB lookups (async)
                embedding = result.get("embedding")
                name = None
                lookalike = None

                if embedding:
                    name = await recognize_face(embedding)
                    matches = await find_lookalike(embedding, top_k=1)
                    if matches and matches[0]["similarity"] > 0.2:
                        lookalike = matches[0]["name"]

                await websocket.send_json({
                    "detected": True,
                    "name": name,
                    "age": result.get("age"),
                    "gender": result.get("gender"),
                    "expression": result.get("expression"),
                    "lookalike": lookalike,
                    "bbox": result.get("bbox"),
                })

            elif action == "register":
                frame_data = msg.get("frame")
                name = msg.get("name", "").strip()
                if not frame_data or not name:
                    await websocket.send_json({"error": "need frame and name"})
                    continue

                img = decode_frame(frame_data)
                if img is None:
                    await websocket.send_json({"error": "decode failed"})
                    continue

                result = await asyncio.to_thread(analyze_face_sync, img)
                if not result["detected"] or not result.get("embedding"):
                    await websocket.send_json({"registered": False, "error": "no face"})
                    continue

                ok = await save_face(
                    name=name,
                    embedding=result["embedding"],
                    age=result.get("age"),
                    gender=result.get("gender"),
                )
                await websocket.send_json({"registered": ok, "name": name})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass
