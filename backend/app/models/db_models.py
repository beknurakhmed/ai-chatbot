from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Date
from ..database import Base


class InteractionLog(Base):
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_name = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    reply = Column(Text, nullable=True)
    locale = Column(String(10), nullable=True)
    mood = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(100), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False, unique=True)
    intent = Column(String(100), nullable=False)
    language = Column(String(10), default="all")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    head_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)  # day_1, week_1, week_2, month_1
    order_num = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmployeeOnboarding(Base):
    __tablename__ = "employee_onboarding"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    task_id = Column(Integer, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PulseSurvey(Base):
    __tablename__ = "pulse_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_name = Column(String(255), nullable=False)
    mood_score = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    category = Column(String(100), default="general")  # general, workload, team, growth
    survey_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
