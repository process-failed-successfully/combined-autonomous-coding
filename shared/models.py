from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from shared.database import Base
import enum

class FileTrack(Base):
    __tablename__ = "file_track"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, unique=True, index=True)
    hash = Column(String)
    last_modified = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # e.g., 'tracked', 'ignored'

class AgentKnowledge(Base):
    __tablename__ = "agent_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True) # QA_BLOCKER, MANAGER_REQUIREMENT, GENERAL_NOTE
    content = Column(Text)
    is_active = Column(Boolean, default=True)
    source_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # PROJECT_SIGNED_OFF, COMPLETED
    value = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentQuestion(Base):
    __tablename__ = "agent_questions"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text)
    answer = Column(Text, nullable=True)
    source_agent = Column(String)
    status = Column(String, default="pending") # pending, answered
    created_at = Column(DateTime, default=datetime.utcnow)

class KeyValueStore(Base):
    __tablename__ = "key_value_store"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text)
