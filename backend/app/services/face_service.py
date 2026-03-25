"""
InsightFace service — local face detection, recognition, attribute & expression analysis.
Expression detection via 68 3D landmarks (no extra model needed).
"""

import json
import numpy as np
from pathlib import Path
from insightface.app import FaceAnalysis
from .celebrity_service import find_lookalike

FACES_DIR = Path(__file__).parent.parent / "data" / "faces"
FACES_DIR.mkdir(parents=True, exist_ok=True)

_app: FaceAnalysis | None = None


def get_face_app() -> FaceAnalysis:
    global _app
    if _app is None:
        _app = FaceAnalysis(
            name="buffalo_l",
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        _app.prepare(ctx_id=0, det_size=(640, 640))
    return _app


def load_known_faces() -> list[dict]:
    faces = []
    for f in FACES_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            faces.append({
                "name": data["name"],
                "embedding": np.array(data["embedding"], dtype=np.float32),
            })
        except Exception:
            continue
    return faces


def save_face_embedding(name: str, embedding: list[float]) -> bool:
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in name).strip()
    if not safe_name:
        return False
    filepath = FACES_DIR / f"{safe_name}_insight.json"
    filepath.write_text(
        json.dumps({"name": name, "embedding": embedding}, ensure_ascii=False),
        encoding="utf-8",
    )
    return True


def recognize_face(embedding: np.ndarray, threshold: float = 0.4) -> str | None:
    known = load_known_faces()
    best_name = None
    best_dist = threshold
    for known_face in known:
        sim = np.dot(embedding, known_face["embedding"]) / (
            np.linalg.norm(embedding) * np.linalg.norm(known_face["embedding"]) + 1e-6
        )
        dist = 1 - sim
        if dist < best_dist:
            best_dist = dist
            best_name = known_face["name"]
    return best_name


def detect_expression(face) -> str:
    """
    Detect expression from InsightFace 3D 68 landmarks.
    Returns: 'happy', 'sad', 'angry', 'surprised', 'neutral'
    """
    lmk = getattr(face, "landmark_3d_68", None)
    if lmk is None or len(lmk) < 68:
        return "neutral"

    # Mouth landmarks (48-67 in 68-point scheme)
    # Outer lip: 48-59, Inner lip: 60-67
    mouth_left = lmk[48][:2]    # left corner
    mouth_right = lmk[54][:2]   # right corner
    mouth_top = lmk[51][:2]     # top center
    mouth_bottom = lmk[57][:2]  # bottom center
    inner_top = lmk[62][:2]     # inner top
    inner_bottom = lmk[66][:2]  # inner bottom

    # Eye landmarks
    left_eye_top = lmk[37][:2]
    left_eye_bottom = lmk[41][:2]
    right_eye_top = lmk[43][:2]
    right_eye_bottom = lmk[47][:2]

    # Eyebrow landmarks
    left_brow_inner = lmk[21][:2]
    right_brow_inner = lmk[22][:2]
    left_brow_outer = lmk[17][:2]
    right_brow_outer = lmk[26][:2]

    # Nose tip for reference
    nose = lmk[30][:2]

    # --- Metrics ---
    mouth_width = np.linalg.norm(mouth_right - mouth_left)
    mouth_height = np.linalg.norm(mouth_top - mouth_bottom)
    inner_mouth_open = np.linalg.norm(inner_top - inner_bottom)
    face_width = np.linalg.norm(lmk[0][:2] - lmk[16][:2])

    # Mouth aspect ratio
    mar = mouth_height / (mouth_width + 1e-6)
    inner_mar = inner_mouth_open / (mouth_width + 1e-6)

    # Smile: mouth corners are higher than mouth center
    mouth_center_y = (mouth_top[1] + mouth_bottom[1]) / 2
    corners_y = (mouth_left[1] + mouth_right[1]) / 2
    smile_ratio = (mouth_center_y - corners_y) / (face_width + 1e-6)

    # Eye openness
    left_ear = np.linalg.norm(left_eye_top - left_eye_bottom) / (face_width + 1e-6)
    right_ear = np.linalg.norm(right_eye_top - right_eye_bottom) / (face_width + 1e-6)
    avg_ear = (left_ear + right_ear) / 2

    # Brow position (lower = angry, higher = surprised)
    left_brow_height = (nose[1] - left_brow_inner[1]) / (face_width + 1e-6)
    right_brow_height = (nose[1] - right_brow_inner[1]) / (face_width + 1e-6)
    avg_brow = (left_brow_height + right_brow_height) / 2

    # Brow squeeze (inner brows close together = angry/sad)
    brow_squeeze = np.linalg.norm(left_brow_inner - right_brow_inner) / (face_width + 1e-6)

    # --- Classification ---
    # Surprised: mouth wide open + eyes wide + brows raised
    if inner_mar > 0.15 and avg_ear > 0.06 and avg_brow > 0.28:
        return "surprised"

    # Happy: smile detected (corners up relative to center)
    if smile_ratio > 0.01 and mar > 0.25:
        return "happy"
    if smile_ratio > 0.015:
        return "happy"

    # Angry: brows low + squeezed + mouth tense
    if avg_brow < 0.2 and brow_squeeze < 0.12:
        return "angry"

    # Sad: corners down, brows inner raised
    if smile_ratio < -0.005 and avg_brow > 0.22:
        return "sad"

    return "neutral"


def analyze_frame(img_bgr: np.ndarray) -> dict:
    app = get_face_app()
    faces = app.get(img_bgr)

    if not faces:
        return {"detected": False}

    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

    bbox = face.bbox.astype(int).tolist()
    age = int(face.age) if hasattr(face, "age") else None
    gender = "M" if getattr(face, "gender", None) == 1 else "F" if getattr(face, "gender", None) == 0 else None
    expression = detect_expression(face)

    embedding = face.embedding if hasattr(face, "embedding") and face.embedding is not None else None
    name = None
    lookalike = None
    if embedding is not None:
        name = recognize_face(embedding)
        # Find celebrity lookalike
        matches = find_lookalike(embedding, top_k=1)
        if matches and matches[0]["similarity"] > 0.2:
            lookalike = matches[0]["name"]

    return {
        "detected": True,
        "name": name,
        "age": age,
        "gender": gender,
        "expression": expression,
        "lookalike": lookalike,
        "bbox": bbox,
        "embedding": embedding.tolist() if embedding is not None else None,
    }
