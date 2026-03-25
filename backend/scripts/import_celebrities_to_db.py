"""Import celebrity embeddings from JSON file into PostgreSQL."""

import sys
import json
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, async_session
from app.models.db_models import CelebrityFace
from sqlalchemy import select


async def main():
    await init_db()

    json_path = Path(__file__).parent.parent / "app" / "data" / "celebrities" / "embeddings.json"
    if not json_path.exists():
        print("No embeddings.json found")
        return

    data = json.loads(json_path.read_text(encoding="utf-8"))
    print(f"Importing {len(data)} celebrities...")

    async with async_session() as db:
        for item in data:
            name = item["name"]
            embedding = item["embedding"]

            result = await db.execute(select(CelebrityFace).where(CelebrityFace.name == name))
            existing = result.scalar_one_or_none()

            if existing:
                existing.embedding = embedding
                print(f"  Updated: {name}")
            else:
                db.add(CelebrityFace(name=name, embedding=embedding))
                print(f"  Added: {name}")

        await db.commit()

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
