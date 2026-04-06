"""Database connection and session management."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://chito:chito@localhost:5432/chito"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    """Create tables and enable pgvector extension."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # Migrations — add missing columns to existing tables
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE buildings ADD COLUMN IF NOT EXISTS photo VARCHAR(500);
            EXCEPTION WHEN duplicate_column THEN NULL;
            END $$;
        """))
