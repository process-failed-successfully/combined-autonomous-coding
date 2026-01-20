import unittest
from pathlib import Path
from shared.knowledge import KnowledgeManager
from shared.database import init_db, SessionLocal
from shared.models import AgentKnowledge, AgentQuestion

class TestKnowledgeManager(unittest.TestCase):

    def setUp(self):
        # Initialize in-memory database for testing
        # We use a string that works with the init_db logic to produce sqlite:///:memory:
        # pathlib.Path(":memory:") works on Linux/Unix to produce ":memory:" string
        init_db(Path(":memory:"))
        self.manager = KnowledgeManager()

    def test_add_and_list_knowledge(self):
        item = self.manager.add_knowledge("Test content", "TEST_CAT")
        self.assertIsNotNone(item.id)
        self.assertEqual(item.content, "Test content")
        self.assertEqual(item.category, "TEST_CAT")

        items = self.manager.list_knowledge()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].content, "Test content")

    def test_filter_knowledge(self):
        self.manager.add_knowledge("Note 1", "CAT_1")
        self.manager.add_knowledge("Note 2", "CAT_2")

        items_1 = self.manager.list_knowledge("CAT_1")
        self.assertEqual(len(items_1), 1)
        self.assertEqual(items_1[0].category, "CAT_1")

        items_2 = self.manager.list_knowledge("CAT_2")
        self.assertEqual(len(items_2), 1)
        self.assertEqual(items_2[0].category, "CAT_2")

    def test_delete_knowledge(self):
        item = self.manager.add_knowledge("To delete")
        deleted = self.manager.delete_knowledge(item.id)
        self.assertTrue(deleted)

        items = self.manager.list_knowledge()
        self.assertEqual(len(items), 0)

    def test_get_and_answer_questions(self):
        # Manually add a question to DB since Manager only reads them (Agents add them)
        # Using SessionLocal explicitly
        db = SessionLocal()
        try:
            q = AgentQuestion(question="What is this?", source_agent="test", status="pending")
            db.add(q)
            db.commit()
            db.refresh(q)
            q_id = q.id
        finally:
            db.close()

        questions = self.manager.get_questions(status="pending")
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].question, "What is this?")

        answered = self.manager.answer_question(q_id, "It is a test.")
        self.assertTrue(answered)

        questions_pending = self.manager.get_questions(status="pending")
        self.assertEqual(len(questions_pending), 0)

        # Check if status updated
        db = SessionLocal()
        try:
            q_updated = db.query(AgentQuestion).filter(AgentQuestion.id == q_id).first()
            self.assertEqual(q_updated.status, "answered")
            self.assertEqual(q_updated.answer, "It is a test.")
        finally:
            db.close()

if __name__ == '__main__':
    unittest.main()
