"""Face database operations using PostgreSQL + pgvector."""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.db_models import KnownFace, CelebrityFace
from ..database import async_session


async def save_face(name: str, embedding: list[float], age: int | None = None, gender: str | None = None) -> bool:
    """Save or update a face in the database."""
    async with async_session() as db:
        # Check if name exists — update embedding
        result = await db.execute(select(KnownFace).where(KnownFace.name == name))
        existing = result.scalar_one_or_none()

        if existing:
            existing.embedding = embedding
            if age:
                existing.age = age
            if gender:
                existing.gender = gender
        else:
            face = KnownFace(name=name, embedding=embedding, age=age, gender=gender)
            db.add(face)

        await db.commit()
        return True


async def recognize_face(embedding: list[float], threshold: float = 0.6) -> str | None:
    """Find closest matching face using pgvector cosine distance."""
    async with async_session() as db:
        # pgvector cosine distance: <=> operator
        # Lower = more similar. threshold 0.6 = cosine similarity > 0.4
        result = await db.execute(
            text("""
                SELECT name, embedding <=> :emb AS distance
                FROM known_faces
                ORDER BY embedding <=> :emb
                LIMIT 1
            """),
            {"emb": str(embedding)},
        )
        row = result.first()
        if row and row.distance < threshold:
            return row.name
        return None


async def find_lookalike(embedding: list[float], top_k: int = 1) -> list[dict]:
    """Find closest celebrity match using pgvector."""
    async with async_session() as db:
        result = await db.execute(
            text("""
                SELECT name, 1 - (embedding <=> :emb) AS similarity
                FROM celebrity_faces
                ORDER BY embedding <=> :emb
                LIMIT :k
            """),
            {"emb": str(embedding), "k": top_k},
        )
        return [{"name": row.name, "similarity": round(row.similarity, 3)} for row in result]


async def list_faces() -> list[dict]:
    """List all registered faces."""
    async with async_session() as db:
        result = await db.execute(select(KnownFace.name, KnownFace.age, KnownFace.gender))
        return [{"name": r.name, "age": r.age, "gender": r.gender} for r in result]


async def import_celebrity(name: str, embedding: list[float]) -> bool:
    """Import a celebrity face embedding."""
    async with async_session() as db:
        result = await db.execute(select(CelebrityFace).where(CelebrityFace.name == name))
        existing = result.scalar_one_or_none()
        if existing:
            existing.embedding = embedding
        else:
            db.add(CelebrityFace(name=name, embedding=embedding))
        await db.commit()
        return True
