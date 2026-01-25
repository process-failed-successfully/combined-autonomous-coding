import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.network import NetworkBuilder, NetworkVisualizer
from shared.map import CodeNode

class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/mock/project")
        self.builder = NetworkBuilder(self.project_dir)

    def test_add_file_nodes(self):
        # Mock scan_project to return some nodes
        with patch("shared.network.scan_project") as mock_scan:
            node = CodeNode("test.py", "module", "test.py", 1)
            mock_scan.return_value = {"test.py": node}

            map_data = self.builder.add_file_nodes()

            self.assertEqual(len(self.builder.nodes), 1)
            # Check if node id is string '0'
            node_id = self.builder.file_to_id["test.py"]
            self.assertEqual(self.builder.nodes[node_id]["label"], "test.py")
            self.assertEqual(self.builder.nodes[node_id]["group"], "file")

    def test_add_import_edges(self):
        # Setup nodes
        with patch("shared.network.scan_project") as mock_scan:
            node_a = CodeNode("a.py", "module", "a.py", 1)
            node_a.dependencies.add("b") # imports b
            node_b = CodeNode("b.py", "module", "b.py", 1)

            mock_scan.return_value = {"a.py": node_a, "b.py": node_b}

            # Populate nodes first
            map_data = self.builder.add_file_nodes()

            self.builder.add_import_edges(map_data)

            self.assertEqual(len(self.builder.edges), 1)
            edge = self.builder.edges[0]

            id_a = self.builder.file_to_id["a.py"]
            id_b = self.builder.file_to_id["b.py"]

            self.assertEqual(edge["from"], id_a)
            self.assertEqual(edge["to"], id_b)
            self.assertEqual(edge["title"], "imports")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_add_git_history(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/git"

        # Mock git log output
        # COMMIT|hash1|Alice
        # a.py
        # b.py
        # (empty line)
        mock_run.return_value.stdout = "COMMIT|hash1|Alice\na.py\nb.py\n"
        mock_run.return_value.returncode = 0

        # Pre-populate file_to_id so the builder knows about these files
        self.builder._get_id("a.py")
        self.builder._get_id("b.py")

        # Mock Path.exists to return True for these files
        # Since project_dir is /mock/project, the check is for /mock/project/a.py
        with patch.object(Path, "exists", return_value=True):
            # Also mock is_dir for the initial check in add_git_history
            with patch.object(Path, "is_dir", return_value=True):
                self.builder.add_git_history()

        # Expect:
        # 1. Author node "Alice"
        # 2. Edges from Alice to a.py and b.py
        # 3. Co-edit edge between a.py and b.py

        author_key = "author:Alice"
        self.assertIn(author_key, self.builder.file_to_id)
        author_id = self.builder.file_to_id[author_key]

        self.assertIn(author_id, self.builder.nodes)
        self.assertEqual(self.builder.nodes[author_id]["group"], "author")

        # Edges
        # Alice -> a.py
        # Alice -> b.py
        # a.py -> b.py (co-edit)

        self.assertEqual(len(self.builder.edges), 3)

        co_edit_edge = next((e for e in self.builder.edges if e.get("dashes") is True), None)
        self.assertIsNotNone(co_edit_edge)
        self.assertEqual(co_edit_edge["value"], 1)

    def test_visualizer_generate_html(self):
        viz = NetworkVisualizer()
        data = {"nodes": [], "edges": []}
        html_output = viz.generate_html(data)

        self.assertIn("<!DOCTYPE HTML>", html_output)
        self.assertIn("vis.Network", html_output)

if __name__ == "__main__":
    unittest.main()
