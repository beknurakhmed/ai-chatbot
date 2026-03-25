"""SQLAlchemy models for PostgreSQL + pgvector."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from pgvector.sqlalchemy import Vector
from ..database import Base


class KnownFace(Base):
    """Registered face for recognition."""
    __tablename__ = "known_faces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    embedding = Column(Vector(512), nullable=False)  # InsightFace = 512-dim
    age = Column(Integer, nullable=True)
    gender = Column(String(1), nullable=True)  # M/F
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CelebrityFace(Base):
    """Celebrity face for lookalike matching."""
    __tablename__ = "celebrity_faces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    embedding = Column(Vector(512), nullable=False)


class InteractionLog(Base):
    """Log of user interactions for analytics."""
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    reply = Column(Text, nullable=True)
    locale = Column(String(10), nullable=True)
    mood = Column(String(50), nullable=True)
    detected_age = Column(Integer, nullable=True)
    detected_gender = Column(String(1), nullable=True)
    detected_expression = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
