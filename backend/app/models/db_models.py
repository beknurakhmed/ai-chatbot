"""SQLAlchemy models for PostgreSQL + pgvector."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
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


class KnowledgeEntry(Base):
    """Knowledge base entry — university info, FAQs, etc."""
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, index=True)  # e.g. general, admission, contacts
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Keyword(Base):
    """Keywords for intent detection in chat."""
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, unique=True)
    intent = Column(String(100), nullable=False)  # e.g. timetable, staff, admission, news, map
    language = Column(String(10), default="all")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TimetableEntry(Base):
    """Individual timetable lesson entry."""
    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group = Column(String(50), nullable=False, index=True)
    day = Column(String(5), nullable=False)      # Mo, Tu, We, Th, Fr
    period = Column(String(5), nullable=False)   # A, B, C, D, E, F, G
    time_str = Column(String(20), nullable=False) # "10:00-11:15"
    subject = Column(String(200), nullable=False)
    teacher = Column(String(200), nullable=True)
    room = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StaffMember(Base):
    """Staff member — parsed from ajou.uz."""
    __tablename__ = "staff_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    position = Column(String(500), nullable=True)
    photo = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)  # leadership, deans, staff, lecturers
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Room(Base):
    """Campus room / classroom."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)  # e.g. "A101", "B203"
    block = Column(String(50), nullable=True)  # e.g. "A Block", "B Block"
    floor = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Building(Base):
    """Campus building / location."""
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    num = Column(Integer, nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    photo = Column(String(500), nullable=True)  # URL or path to building photo
    color = Column(String(50), default="bg-blue-500")  # Tailwind class
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NewsItem(Base):
    """News articles parsed from ajou.uz."""
    __tablename__ = "news_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(Integer, nullable=True, unique=True)  # id from ajou.uz URL
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
