"""
Build celebrity face embeddings database.

Usage:
  1. Auto-download from LFW dataset (Labeled Faces in the Wild):
     python scripts/build_celebrity_db.py --lfw

  2. From a local folder of images (Name_Surname.jpg or Name/001.jpg):
     python scripts/build_celebrity_db.py --folder path/to/photos

  3. From a CSV with name,url pairs:
     python scripts/build_celebrity_db.py --csv celebrities.csv

Images are processed through InsightFace to extract embeddings.
Output: app/data/celebrities/embeddings.json
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import cv2


def get_face_app():
    from insightface.app import FaceAnalysis
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(640, 640))
    return app


def extract_embedding(app, img_path: str) -> np.ndarray | None:
    """Extract face embedding from an image file."""
    img = cv2.imread(img_path)
    if img is None:
        return None
    faces = app.get(img)
    if not faces:
        return None
    # Take largest face
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    if face.embedding is None:
        return None
    return face.embedding


def download_lfw(target_dir: Path, min_images: int = 5):
    """Download LFW dataset (only people with min_images photos)."""
    from sklearn.datasets import fetch_lfw_people
    print("Downloading LFW dataset (this may take a few minutes)...")
    lfw = fetch_lfw_people(min_faces_per_person=min_images, resize=1.0)

    target_dir.mkdir(parents=True, exist_ok=True)
    names = lfw.target_names

    # Save one image per person
    saved = set()
    for img, label in zip(lfw.images, lfw.target):
        name = names[label]
        if name in saved:
            continue
        saved.add(name)

        img_uint8 = (img * 255).astype(np.uint8) if img.max() <= 1.0 else img.astype(np.uint8)
        filename = name.replace(" ", "_") + ".jpg"
        filepath = target_dir / filename
        cv2.imwrite(str(filepath), img_uint8)

    print(f"Saved {len(saved)} celebrity photos to {target_dir}")
    return target_dir


def build_from_folder(app, folder: Path) -> list[dict]:
    """Build embeddings from a folder of images."""
    results = []
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    files = []
    # Check for subfolders (Name/001.jpg) or flat (Name_Surname.jpg)
    for item in sorted(folder.iterdir()):
        if item.is_dir():
            for f in sorted(item.iterdir()):
                if f.suffix.lower() in extensions:
                    name = item.name.replace("_", " ")
                    files.append((name, f))
        elif item.suffix.lower() in extensions:
            name = item.stem.replace("_", " ")
            files.append((name, item))

    print(f"Processing {len(files)} images...")

    for i, (name, filepath) in enumerate(files):
        emb = extract_embedding(app, str(filepath))
        if emb is not None:
            results.append({
                "name": name,
                "embedding": emb.tolist(),
            })
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(files)} processed ({len(results)} faces found)")
        else:
            print(f"  No face found: {filepath.name}")

    print(f"Extracted {len(results)} celebrity embeddings from {len(files)} images")
    return results


def build_from_csv(app, csv_path: Path, download_dir: Path) -> list[dict]:
    """Build embeddings from CSV with name,url columns."""
    import urllib.request

    download_dir.mkdir(parents=True, exist_ok=True)

    with open(csv_path, encoding="utf-8") as f:
        lines = [l.strip().split(",", 1) for l in f if l.strip() and not l.startswith("#")]

    print(f"Downloading {len(lines)} celebrity photos...")

    for name, url in lines:
        safe_name = name.strip().replace(" ", "_")
        filepath = download_dir / f"{safe_name}.jpg"
        if filepath.exists():
            continue
        try:
            urllib.request.urlretrieve(url.strip(), str(filepath))
            print(f"  Downloaded: {name.strip()}")
        except Exception as e:
            print(f"  Failed: {name.strip()} - {e}")

    return build_from_folder(app, download_dir)


def main():
    parser = argparse.ArgumentParser(description="Build celebrity embeddings database")
    parser.add_argument("--lfw", action="store_true", help="Download and use LFW dataset")
    parser.add_argument("--folder", type=str, help="Path to folder with celebrity photos")
    parser.add_argument("--csv", type=str, help="Path to CSV with name,url pairs")
    parser.add_argument("--min-faces", type=int, default=10, help="Min images per person for LFW (default: 10)")
    args = parser.parse_args()

    output_path = Path(__file__).parent.parent / "app" / "data" / "celebrities" / "embeddings.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    photos_dir = output_path.parent / "photos"

    print("Loading InsightFace model...")
    app = get_face_app()

    results = []

    if args.lfw:
        lfw_dir = download_lfw(photos_dir, min_images=args.min_faces)
        results = build_from_folder(app, lfw_dir)
    elif args.folder:
        results = build_from_folder(app, Path(args.folder))
    elif args.csv:
        results = build_from_csv(app, Path(args.csv), photos_dir)
    else:
        # Default: process photos dir if it has images
        if photos_dir.exists() and any(photos_dir.iterdir()):
            results = build_from_folder(app, photos_dir)
        else:
            print("No source specified. Options:")
            print("  --lfw              Download LFW dataset (~170 celebrities)")
            print("  --folder PATH      Use local folder with photos")
            print("  --csv PATH         Use CSV with name,url pairs")
            print(f"\nOr put photos in: {photos_dir}")
            print("  Format: Name_Surname.jpg or Name/photo.jpg")
            return

    # Deduplicate: average embeddings for same person
    merged: dict[str, list] = {}
    for r in results:
        merged.setdefault(r["name"], []).append(np.array(r["embedding"]))

    final = []
    for name, embs in merged.items():
        avg_emb = np.mean(embs, axis=0)
        avg_emb = avg_emb / (np.linalg.norm(avg_emb) + 1e-6)  # normalize
        final.append({"name": name, "embedding": avg_emb.tolist()})

    output_path.write_text(
        json.dumps(final, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nSaved {len(final)} celebrity embeddings to {output_path}")


if __name__ == "__main__":
    main()
