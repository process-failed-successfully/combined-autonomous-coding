import unittest
from pathlib import Path
import json
from shared.knowledge import KnowledgeManager
from shared.database import init_db
from shared.knowledge_graph import generate_knowledge_graph

class TestKnowledgeGraph(unittest.TestCase):

    def setUp(self):
        # Initialize in-memory database for testing
        init_db(Path(":memory:"))
        self.manager = KnowledgeManager()
        self.manager.add_knowledge("Note A", "CAT_1")
        self.manager.add_knowledge("Note B", "CAT_1")
        self.manager.add_knowledge("Note C", "CAT_2")

    def test_json_output(self):
        output = generate_knowledge_graph(Path("."), output_format="json")
        data = json.loads(output)
        self.assertEqual(len(data), 3)
        # Order is not guaranteed, so check existence
        contents = [item['content'] for item in data]
        self.assertIn("Note A", contents)
        self.assertIn("Note B", contents)
        self.assertIn("Note C", contents)

    def test_mermaid_output(self):
        output = generate_knowledge_graph(Path("."), output_format="mermaid")
        self.assertIn("graph TD", output)
        self.assertIn("subgraph CAT_1", output)
        self.assertIn("subgraph CAT_2", output)
        self.assertIn("Note A", output)

    def test_html_output_content(self):
        output_file = Path("test_graph.html")
        msg = generate_knowledge_graph(Path("."), output_format="html", output_file=output_file)
        self.assertIn("Interactive graph saved", msg)
        self.assertTrue(output_file.exists())

        content = output_file.read_text()
        self.assertIn("vis.Network", content)
        self.assertIn("CAT_1", content)

        # Cleanup
        if output_file.exists():
            output_file.unlink()

if __name__ == '__main__':
    unittest.main()
