from typing import List, Optional
from sqlalchemy.orm import Session
from shared.database import SessionLocal
from shared.models import AgentKnowledge, AgentQuestion

class KnowledgeManager:
    """
    Manages the agent's knowledge base and pending questions.
    """

    def __init__(self):
        pass

    def add_knowledge(self, content: str, category: str = "GENERAL_NOTE", source: str = "user") -> AgentKnowledge:
        """Adds a new piece of knowledge to the database."""
        db: Session = SessionLocal()
        try:
            item = AgentKnowledge(
                content=content,
                category=category,
                source_agent=source,
                is_active=True
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item
        finally:
            db.close()

    def list_knowledge(self, category: Optional[str] = None) -> List[AgentKnowledge]:
        """Lists active knowledge items, optionally filtered by category."""
        db: Session = SessionLocal()
        try:
            query = db.query(AgentKnowledge).filter(AgentKnowledge.is_active == True)
            if category:
                query = query.filter(AgentKnowledge.category == category)
            return query.all()
        finally:
            db.close()

    def delete_knowledge(self, knowledge_id: int) -> bool:
        """Soft-deletes a knowledge item (sets is_active=False)."""
        db: Session = SessionLocal()
        try:
            item = db.query(AgentKnowledge).filter(AgentKnowledge.id == knowledge_id).first()
            if item:
                item.is_active = False  # type: ignore
                db.commit()
                return True
            return False
        finally:
            db.close()

    def get_questions(self, status: str = "pending") -> List[AgentQuestion]:
        """Retrieves questions asked by the agent."""
        db: Session = SessionLocal()
        try:
            return db.query(AgentQuestion).filter(AgentQuestion.status == status).all()
        finally:
            db.close()

    def answer_question(self, question_id: int, answer: str) -> bool:
        """Answers a pending question."""
        db: Session = SessionLocal()
        try:
            item = db.query(AgentQuestion).filter(AgentQuestion.id == question_id).first()
            if item:
                item.answer = answer  # type: ignore
                item.status = "answered"  # type: ignore
                db.commit()
                return True
            return False
        finally:
            db.close()
