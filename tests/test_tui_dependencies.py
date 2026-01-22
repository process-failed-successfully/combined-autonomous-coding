import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Tree
from shared.tui import AgentTUI, DependenciesTab

class TestTUIDependencies(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "project"
        self.project_dir.mkdir()

        # Mock dependencies analyzer
        self.patcher_analyzer = patch("shared.tui.DependencyAnalyzer")
        self.MockAnalyzer = self.patcher_analyzer.start()
        self.mock_analyzer = self.MockAnalyzer.return_value

    def tearDown(self):
        self.patcher_analyzer.stop()
        shutil.rmtree(self.test_dir)

    async def test_dependencies_tab_structure(self):
        """Test the dependencies tab structure."""
        app = AgentTUI(project_dir=self.project_dir)
        async with app.run_test() as pilot:
            # Check if TabPane exists (it's inside TabbedContent)
            self.assertTrue(app.query_one("#tab-deps"))
            pass

    async def test_dependencies_tab_logic(self):
        """Test logic of DependenciesTab isolated."""

        # Setup mock data
        self.mock_analyzer.scan.return_value = {
            "python": [
                {
                    "source": "requirements.txt",
                    "dependencies": [
                        {"name": "requests", "version": "==2.0.0"}
                    ]
                }
            ],
            "node": []
        }

        tab = DependenciesTab(self.project_dir)
        # Mock notify to prevent NoActiveAppError
        tab.notify = MagicMock()

        # Mock UI elements
        mock_status = MagicMock(spec=Label)
        mock_tree = MagicMock(spec=Tree)

        # Setup tree mock to handle add calls
        mock_root = MagicMock()
        mock_tree.root = mock_root

        # Mock return for add() calls to return new nodes
        mock_py_node = MagicMock()
        mock_file_node = MagicMock()
        mock_root.add.return_value = mock_py_node
        mock_py_node.add.return_value = mock_file_node

        # We mock query_one to return our mocks
        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#deps-status": mock_status,
            "#deps-tree": mock_tree
        }.get(selector))

        # Test on_mount (load_deps)
        tab.on_mount()

        self.mock_analyzer.scan.assert_called_once()
        mock_tree.clear.assert_called()

        # Verify Python node added
        mock_root.add.assert_called()
        args = mock_root.add.call_args[0]
        self.assertIn("Python", args[0])

        # Verify file node added
        mock_py_node.add.assert_called()

        # Verify dependency node added to file node
        mock_file_node.add.assert_called()
        dep_args = mock_file_node.add.call_args[0]
        self.assertIn("requests", dep_args[0])

    async def test_check_updates_logic(self):
        """Test check updates button logic."""
        tab = DependenciesTab(self.project_dir)
        # Mock notify to prevent NoActiveAppError
        tab.notify = MagicMock()

        # Mock UI
        mock_status = MagicMock(spec=Label)
        mock_tree = MagicMock(spec=Tree)
        mock_root = MagicMock()
        mock_tree.root = mock_root

        # Mock node adding
        mock_py_node = MagicMock()
        mock_file_node = MagicMock()
        mock_root.add.return_value = mock_py_node
        mock_py_node.add.return_value = mock_file_node

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#deps-status": mock_status,
            "#deps-tree": mock_tree
        }.get(selector))

        # Mock analyzer
        self.mock_analyzer.scan.return_value = {
            "python": [{"source": "r.txt", "dependencies": [{"name": "pkg", "version": "1.0"}]}],
            "node": []
        }

        # Mock check_updates return
        updated_data = {
            "python": [{"source": "r.txt", "dependencies": [{"name": "pkg", "version": "1.0", "latest": "2.0", "outdated": True}]}],
            "node": []
        }
        self.mock_analyzer.check_updates.return_value = updated_data

        # Call check_updates
        await tab.check_updates()

        # Verify
        self.mock_analyzer.check_updates.assert_called()
        mock_status.update.assert_called_with("Update check complete.")

        # Verify tree was re-populated
        # We expect root.add to be called for Python
        mock_root.add.assert_called()

        # We expect the file node to have the dependency added, and since it is outdated, it should look different or have data
        # The logic in load_deps calls add_dep_node which calls parent_node.add(label, data=...)
        mock_file_node.add.assert_called()
        call_args = mock_file_node.add.call_args
        label = call_args[0][0]
        # Check for red color tag or similar indicating outdated
        self.assertIn("red", label)

if __name__ == "__main__":
    unittest.main()
