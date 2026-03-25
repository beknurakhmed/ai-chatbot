"""
Download celebrity photos from Wikipedia/Wikimedia and build embeddings.
Uses high-res photos that InsightFace can process.
"""

import sys
import json
import urllib.request
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np

PHOTOS_DIR = Path(__file__).parent.parent / "app" / "data" / "celebrities" / "photos"
OUTPUT_PATH = Path(__file__).parent.parent / "app" / "data" / "celebrities" / "embeddings.json"

# Curated list: name → direct image URL (Wikimedia Commons, public domain / CC)
CELEBRITIES = {
    # Actors
    "Tom Cruise": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/Tom_Cruise_by_Gage_Skidmore_2.jpg/440px-Tom_Cruise_by_Gage_Skidmore_2.jpg",
    "Brad Pitt": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Brad_Pitt_2019_by_Glenn_Francis.jpg/440px-Brad_Pitt_2019_by_Glenn_Francis.jpg",
    "Leonardo DiCaprio": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Leonardo_Dicaprio_Cannes_2019.jpg/440px-Leonardo_Dicaprio_Cannes_2019.jpg",
    "Johnny Depp": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Johnny_Depp-2757_%28cropped%29.jpg/440px-Johnny_Depp-2757_%28cropped%29.jpg",
    "Robert Downey Jr.": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/Robert_Downey_Jr_2014_Comic_Con_%28cropped%29.jpg/440px-Robert_Downey_Jr_2014_Comic_Con_%28cropped%29.jpg",
    "Keanu Reeves": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/Keanu_Reeves_2023.jpg/440px-Keanu_Reeves_2023.jpg",
    "Will Smith": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/TechCrunch_Disrupt_2019_%2848834434641%29_%28cropped%29.jpg/440px-TechCrunch_Disrupt_2019_%2848834434641%29_%28cropped%29.jpg",
    "Dwayne Johnson": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Dwayne_Johnson_2014_%28cropped%29.jpg/440px-Dwayne_Johnson_2014_%28cropped%29.jpg",
    "Chris Hemsworth": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Chris_Hemsworth_by_Gage_Skidmore_2_%28cropped%29.jpg/440px-Chris_Hemsworth_by_Gage_Skidmore_2_%28cropped%29.jpg",
    "Scarlett Johansson": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Scarlett_Johansson_by_Gage_Skidmore_2_%28cropped%2C_2%29.jpg/440px-Scarlett_Johansson_by_Gage_Skidmore_2_%28cropped%2C_2%29.jpg",
    "Angelina Jolie": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ad/Angelina_Jolie_2_June_2014_%28cropped%29.jpg/440px-Angelina_Jolie_2_June_2014_%28cropped%29.jpg",
    "Emma Watson": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Emma_Watson_2013.jpg/440px-Emma_Watson_2013.jpg",
    # Musicians
    "Eminem": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Eminem_-_Concert_for_Valor_in_Washington%2C_D.C._Nov._11%2C_2014_%282%29_%28Cropped%29.jpg/440px-Eminem_-_Concert_for_Valor_in_Washington%2C_D.C._Nov._11%2C_2014_%282%29_%28Cropped%29.jpg",
    "Ed Sheeran": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Ed_Sheeran-6886_%28cropped%29.jpg/440px-Ed_Sheeran-6886_%28cropped%29.jpg",
    "Taylor Swift": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Taylor_Swift_at_the_2023_MTV_Video_Music_Awards_%283%29.png/440px-Taylor_Swift_at_the_2023_MTV_Video_Music_Awards_%283%29.png",
    # Sports
    "Cristiano Ronaldo": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Cristiano_Ronaldo_2018.jpg/440px-Cristiano_Ronaldo_2018.jpg",
    "Lionel Messi": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Lionel-Messi-Argentina-2022-FIFA-World-Cup_%28cropped%29.jpg/440px-Lionel-Messi-Argentina-2022-FIFA-World-Cup_%28cropped%29.jpg",
    "Neymar": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/20180610_FIFA_Friendly_Match_Austria_vs._Brazil_Neymar_850_1705_%28cropped%29.jpg/440px-20180610_FIFA_Friendly_Match_Austria_vs._Brazil_Neymar_850_1705_%28cropped%29.jpg",
    # Korean celebrities
    "BTS Jungkook": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Jungkook_at_the_White_House.jpg/440px-Jungkook_at_the_White_House.jpg",
    "BTS V": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/V_at_the_White_House.jpg/440px-V_at_the_White_House.jpg",
    "BTS RM": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/RM_at_the_White_House.jpg/440px-RM_at_the_White_House.jpg",
    "BLACKPINK Jennie": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Jennie_Kim_for_Marie_Claire_Korea_October_2023_issue.jpg/440px-Jennie_Kim_for_Marie_Claire_Korea_October_2023_issue.jpg",
    "Lee Min-ho": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0d/Lee_Min-ho_at_Incheon_Airport%2C_6_October_2012_01.jpg/440px-Lee_Min-ho_at_Incheon_Airport%2C_6_October_2012_01.jpg",
    "Song Joong-ki": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/de/Song_Joong-ki_at_Style_Icon_Asia_2016.jpg/440px-Song_Joong-ki_at_Style_Icon_Asia_2016.jpg",
    # Tech/Business
    "Elon Musk": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Elon_Musk_Royal_Society_%28crop2%29.jpg/440px-Elon_Musk_Royal_Society_%28crop2%29.jpg",
    "Mark Zuckerberg": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Mark_Zuckerberg_F8_2019_Keynote_%2832830578717%29_%28cropped%29.jpg/440px-Mark_Zuckerberg_F8_2019_Keynote_%2832830578717%29_%28cropped%29.jpg",
    # Central Asian
    "Shavkat Mirziyoyev": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c6/Shavkat_Mirziyoyev_%282018-04-08%29.jpg/440px-Shavkat_Mirziyoyev_%282018-04-08%29.jpg",
    "Islom Karimov": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Islam_Karimov_2016.jpg/440px-Islam_Karimov_2016.jpg",
}


def download_photos():
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (ChitoBot/1.0; educational project)"}

    for name, url in CELEBRITIES.items():
        safe_name = name.replace(" ", "_").replace("/", "_")
        filepath = PHOTOS_DIR / f"{safe_name}.jpg"
        if filepath.exists():
            print(f"  Already exists: {name}")
            continue
        try:
            req = urllib.request.Request(url, headers=headers)
            data = urllib.request.urlopen(req, timeout=15).read()
            filepath.write_bytes(data)
            print(f"  Downloaded: {name}")
        except Exception as e:
            print(f"  FAILED: {name} — {e}")


def build_embeddings():
    from insightface.app import FaceAnalysis

    print("Loading InsightFace...")
    app = FaceAnalysis(
        name="buffalo_l",
        providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    app.prepare(ctx_id=0, det_size=(640, 640))

    results = []
    extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for filepath in sorted(PHOTOS_DIR.iterdir()):
        if filepath.suffix.lower() not in extensions:
            continue
        name = filepath.stem.replace("_", " ")

        img = cv2.imread(str(filepath))
        if img is None:
            print(f"  Can't read: {filepath.name}")
            continue

        faces = app.get(img)
        if not faces:
            print(f"  No face: {name}")
            continue

        face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
        if face.embedding is None:
            print(f"  No embedding: {name}")
            continue

        emb = face.embedding / (np.linalg.norm(face.embedding) + 1e-6)
        results.append({"name": name, "embedding": emb.tolist()})
        print(f"  OK: {name}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {len(results)} celebrity embeddings to {OUTPUT_PATH}")


if __name__ == "__main__":
    print("=== Downloading celebrity photos ===")
    download_photos()
    print("\n=== Building embeddings ===")
    build_embeddings()
