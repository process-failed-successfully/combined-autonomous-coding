from typing import List, Optional
import requests
from bs4 import BeautifulSoup
from pathlib import Path
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
                item.is_active = False
                db.commit()
                return True
            return False
        finally:
            db.close()

    def ingest_knowledge(self, source: str, category: str = "LEARNING") -> AgentKnowledge:
        """
        Ingests knowledge from a file path or URL.
        """
        content = ""
        source_type = "user"

        if source.startswith("http://") or source.startswith("https://"):
            try:
                response = requests.get(source, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                content = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = '\n'.join(chunk for chunk in chunks if chunk)
                source_type = f"url:{source}"
            except Exception as e:
                raise ValueError(f"Failed to fetch URL {source}: {e}")
        else:
            # Assume file path
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {source}")
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
                source_type = f"file:{path.name}"
            except Exception as e:
                raise ValueError(f"Failed to read file {source}: {e}")

        if not content:
             raise ValueError("No content found.")

        return self.add_knowledge(content, category=category, source=source_type)

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
                item.answer = answer
                item.status = "answered"
                db.commit()
                return True
            return False
        finally:
            db.close()
