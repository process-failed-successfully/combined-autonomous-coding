from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from shared.database import SessionLocal
from shared.models import AgentKnowledge, AgentQuestion, KnowledgeLink

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

    def update_knowledge(self, knowledge_id: int, content: str) -> bool:
        """Updates the content of a knowledge item."""
        db: Session = SessionLocal()
        try:
            item = db.query(AgentKnowledge).filter(AgentKnowledge.id == knowledge_id).first()
            if item:
                item.content = content
                db.commit()
                return True
            return False
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

    def link_items(self, source_id: int, target_id: int, relation_type: str = "related_to") -> bool:
        """Links two knowledge items."""
        if source_id == target_id:
            return False

        db: Session = SessionLocal()
        try:
            # Check if link exists
            exists = db.query(KnowledgeLink).filter(
                KnowledgeLink.source_id == source_id,
                KnowledgeLink.target_id == target_id
            ).first()

            if exists:
                return True

            link = KnowledgeLink(source_id=source_id, target_id=target_id, relation_type=relation_type)
            db.add(link)
            db.commit()
            return True
        except Exception:
            return False
        finally:
            db.close()

    def unlink_items(self, link_id: int) -> bool:
        """Removes a link."""
        db: Session = SessionLocal()
        try:
            link = db.query(KnowledgeLink).filter(KnowledgeLink.id == link_id).first()
            if link:
                db.delete(link)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def get_links_for_item(self, item_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Returns incoming and outgoing links for an item."""
        db: Session = SessionLocal()
        try:
            outgoing = db.query(KnowledgeLink).filter(KnowledgeLink.source_id == item_id).all()
            incoming = db.query(KnowledgeLink).filter(KnowledgeLink.target_id == item_id).all()

            # Enrich with target/source details
            outgoing_data = []
            for link in outgoing:
                target = db.query(AgentKnowledge).filter(AgentKnowledge.id == link.target_id).first()
                if target:
                    outgoing_data.append({
                        "link_id": link.id,
                        "target_id": target.id,
                        "content": target.content,
                        "relation": link.relation_type
                    })

            incoming_data = []
            for link in incoming:
                source = db.query(AgentKnowledge).filter(AgentKnowledge.id == link.source_id).first()
                if source:
                    incoming_data.append({
                        "link_id": link.id,
                        "source_id": source.id,
                        "content": source.content,
                        "relation": link.relation_type
                    })

            return {"outgoing": outgoing_data, "incoming": incoming_data}
        finally:
            db.close()

    def search_knowledge(self, query: str) -> List[AgentKnowledge]:
        """Simple text search for knowledge items."""
        db: Session = SessionLocal()
        try:
            # Case insensitive search using ilike
            # For SQLite, LIKE is case-insensitive for ASCII by default, but we can assume standard behavior
            return db.query(AgentKnowledge).filter(
                AgentKnowledge.is_active == True,
                or_(
                    AgentKnowledge.content.ilike(f"%{query}%"),
                    AgentKnowledge.category.ilike(f"%{query}%")
                )
            ).all()
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
                item.answer = answer
                item.status = "answered"
                db.commit()
                return True
            return False
        finally:
            db.close()
