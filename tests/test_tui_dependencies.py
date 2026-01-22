import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import shutil
import tempfile

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, Tree
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
        mock_tree = MagicMock(spec=Tree)
        mock_tree.root = MagicMock()
        mock_status = MagicMock(spec=Label)

        # We mock query_one to return our mocks
        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#deps-tree": mock_tree,
            "#deps-status": mock_status
        }.get(selector))

        # Test on_mount (load_deps)
        tab.on_mount()

        self.mock_analyzer.scan.assert_called_once()
        mock_tree.clear.assert_called()
        mock_tree.root.expand.assert_called()

        # Verify node addition
        # tree.root.add("🐍 Python", expand=True)
        # We check one call
        add_calls = mock_tree.root.add.call_args_list
        self.assertTrue(len(add_calls) > 0)
        # Check that one of the calls was for Python
        self.assertTrue(any("Python" in str(c) for c in add_calls))

    async def test_check_updates_logic(self):
        """Test check updates button logic."""
        tab = DependenciesTab(self.project_dir)
        # Mock notify to prevent NoActiveAppError
        tab.notify = MagicMock()

        # Mock UI
        mock_tree = MagicMock(spec=Tree)
        mock_tree.root = MagicMock()
        mock_status = MagicMock(spec=Label)

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#deps-tree": mock_tree,
            "#deps-status": mock_status
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

        # Verify tree update (it calls load_deps which calls tree.root.add)
        add_calls = mock_tree.root.add.call_args_list
        self.assertTrue(len(add_calls) > 0)

if __name__ == "__main__":
    unittest.main()
