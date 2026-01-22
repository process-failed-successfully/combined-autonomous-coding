import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Tree, RichLog, Input
from shared.tui import CodeMapTab
from shared.map import CodeNode

class TestCodeMapTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)

    @patch("shared.tui.scan_project")
    async def test_codemap_population(self, mock_scan):
        """Test that the tree is populated from scan_project data."""
        # Setup mock data
        node_module = CodeNode("test.py", "module", "test.py", 1)
        node_class = CodeNode("TestClass", "class", "test.py", 5, end_lineno=10)
        node_func = CodeNode("test_func", "function", "test.py", 12, end_lineno=15)

        node_module.children.append(node_class)
        node_module.children.append(node_func)

        mock_scan.return_value = {"test.py": node_module}

        tab = CodeMapTab(self.project_dir)

        # Mock widgets
        mock_tree = MagicMock(spec=Tree)
        mock_tree.root = MagicMock()
        mock_tree.root.add.return_value = MagicMock() # file node
        mock_tree.root.add.return_value.add.return_value = MagicMock() # class node

        tab.query_one = MagicMock(return_value=mock_tree)

        tab.on_mount()

        mock_scan.assert_called_once()
        mock_tree.clear.assert_called_once()

        # Verify nodes added
        # Root add called for file
        mock_tree.root.add.assert_called()
        args, kwargs = mock_tree.root.add.call_args
        self.assertIn("test.py", args[0])
        self.assertEqual(kwargs['data'], node_module)

    @patch("shared.tui.scan_project")
    async def test_codemap_filtering(self, mock_scan):
        """Test that filtering updates the tree."""
        node_module = CodeNode("test.py", "module", "test.py", 1)
        node_class = CodeNode("TestClass", "class", "test.py", 5)
        node_module.children.append(node_class)

        mock_scan.return_value = {"test.py": node_module}

        tab = CodeMapTab(self.project_dir)
        tab.map_data = mock_scan.return_value

        mock_tree = MagicMock(spec=Tree)
        mock_tree.root = MagicMock()
        mock_tree.root.add.return_value = MagicMock()
        tab.query_one = MagicMock(return_value=mock_tree)

        # Filter matches nothing
        tab.populate_tree(filter_text="NotFound")
        mock_tree.root.add.assert_not_called()

        # Filter matches class
        tab.populate_tree(filter_text="TestClass")
        mock_tree.root.add.assert_called()

    @patch("shared.tui.scan_project")
    async def test_codemap_selection(self, mock_scan):
        """Test that selecting a node updates the preview."""
        tab = CodeMapTab(self.project_dir)

        mock_preview = MagicMock(spec=RichLog)
        tab.query_one = MagicMock(return_value=mock_preview)

        # Mock file system
        file_path = self.project_dir / "test.py"
        file_path.write_text("line1\nline2\nline3\nline4\nline5", encoding="utf-8")

        # Mock event
        mock_event = MagicMock()
        node_data = CodeNode("Test", "class", "test.py", 2, end_lineno=4)
        mock_event.node.data = node_data

        tab.on_node_selected(mock_event)

        mock_preview.clear.assert_called_once()
        # Verify write called with formatted text and syntax
        self.assertTrue(mock_preview.write.called)

        # We can't easily check the content of RichLog write because it might be a Renderable
        # But we can check that it didn't fail

if __name__ == "__main__":
    unittest.main()
