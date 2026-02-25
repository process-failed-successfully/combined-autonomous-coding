import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.models import AgentKnowledge
from shared.knowledge_graph import generate_knowledge_graph

class TestKnowledgeGraphExport(unittest.TestCase):
    def setUp(self):
        # Mock items
        self.item1 = AgentKnowledge(id=1, category="CAT1", content="Content 1", source_agent="agent1")
        self.item2 = AgentKnowledge(id=2, category="CAT2", content="Content 2", source_agent="agent2")
        self.items = [self.item1, self.item2]

    @patch("shared.knowledge_graph.KnowledgeManager")
    def test_generate_json(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_knowledge.return_value = self.items

        result = generate_knowledge_graph(Path("."), output_format="json")
        self.assertIn('"id": 1', result)
        self.assertIn('"content": "Content 1"', result)

    @patch("shared.knowledge_graph.KnowledgeManager")
    def test_generate_mermaid(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_knowledge.return_value = self.items

        result = generate_knowledge_graph(Path("."), output_format="mermaid")
        self.assertIn("graph TD", result)
        self.assertIn("subgraph CAT1", result)
        self.assertIn('k1("Content 1")', result)

    @patch("shared.knowledge_graph.KnowledgeManager")
    def test_generate_html_file(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.list_knowledge.return_value = self.items

        with patch("pathlib.Path.write_text") as mock_write:
            result = generate_knowledge_graph(Path("."), output_format="html")

            # Check if write_text was called
            mock_write.assert_called()
            # Check content passed to write_text
            content = mock_write.call_args[0][0]
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("vis.DataSet", content)
            self.assertIn('"id": "item_1"', content)

if __name__ == '__main__':
    unittest.main()
