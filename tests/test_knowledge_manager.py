import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.models import AgentKnowledge, KnowledgeLink
from shared.knowledge import KnowledgeManager

class TestKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        # Use in-memory SQLite for testing
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

        # Patch SessionLocal in manager
        self.patcher = patch('shared.knowledge.SessionLocal', self.Session)
        self.mock_session = self.patcher.start()

        self.manager = KnowledgeManager()

    def tearDown(self):
        self.patcher.stop()
        Base.metadata.drop_all(self.engine)

    def test_link_creation(self):
        # Create two nodes
        node1 = self.manager.add_knowledge("Node 1", category="TEST")
        node2 = self.manager.add_knowledge("Node 2", category="TEST")

        # Link them
        success = self.manager.link_items(node1.id, node2.id, relation_type="related_to")
        self.assertTrue(success)

        # Verify in DB
        session = self.Session()
        link = session.query(KnowledgeLink).first()
        self.assertIsNotNone(link)
        self.assertEqual(link.source_id, node1.id)
        self.assertEqual(link.target_id, node2.id)
        self.assertEqual(link.relation_type, "related_to")
        session.close()

    def test_get_links(self):
        node1 = self.manager.add_knowledge("Node 1", category="TEST")
        node2 = self.manager.add_knowledge("Node 2", category="TEST")
        node3 = self.manager.add_knowledge("Node 3", category="TEST")

        self.manager.link_items(node1.id, node2.id, "relates")
        self.manager.link_items(node3.id, node1.id, "depends_on")

        links = self.manager.get_links_for_item(node1.id)

        self.assertEqual(len(links["outgoing"]), 1)
        self.assertEqual(links["outgoing"][0]["target_id"], node2.id)
        self.assertEqual(links["outgoing"][0]["relation"], "relates")

        self.assertEqual(len(links["incoming"]), 1)
        self.assertEqual(links["incoming"][0]["source_id"], node3.id)
        self.assertEqual(links["incoming"][0]["relation"], "depends_on")

    def test_unlink(self):
        node1 = self.manager.add_knowledge("Node 1")
        node2 = self.manager.add_knowledge("Node 2")
        self.manager.link_items(node1.id, node2.id)

        links = self.manager.get_links_for_item(node1.id)
        link_id = links["outgoing"][0]["link_id"]

        success = self.manager.unlink_items(link_id)
        self.assertTrue(success)

        links_after = self.manager.get_links_for_item(node1.id)
        self.assertEqual(len(links_after["outgoing"]), 0)

    def test_search(self):
        self.manager.add_knowledge("Apple Pie Recipe", category="COOKING")
        self.manager.add_knowledge("Python Script", category="CODING")

        results = self.manager.search_knowledge("Pie")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Apple Pie Recipe")

        results_cat = self.manager.search_knowledge("CODING")
        self.assertEqual(len(results_cat), 1)
        self.assertEqual(results_cat[0].content, "Python Script")

if __name__ == '__main__':
    unittest.main()
