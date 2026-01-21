import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from textual.widgets import Label, DataTable
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
        async with app.run_test() as _:
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
        setattr(tab, 'notify', MagicMock())

        # Mock UI elements
        mock_table = MagicMock(spec=DataTable)
        mock_status = MagicMock(spec=Label)

        # We mock query_one to return our mocks
        setattr(tab, 'query_one', MagicMock(side_effect=lambda selector, type=None: {
            "#deps-table": mock_table,
            "#deps-status": mock_status
        }.get(selector)))

        # Test on_mount (load_deps)
        tab.on_mount()

        self.mock_analyzer.scan.assert_called_once()
        mock_table.add_columns.assert_called()
        mock_table.clear.assert_called()
        # Verify row addition
        # "Python", "requests", "==2.0.0", "prod", "-", "OK"
        # We check one call
        add_row_calls = mock_table.add_row.call_args_list
        self.assertTrue(len(add_row_calls) > 0)
        self.assertEqual(add_row_calls[0][0][1], "requests")

    async def test_check_updates_logic(self):
        """Test check updates button logic."""
        tab = DependenciesTab(self.project_dir)
        # Mock notify to prevent NoActiveAppError
        setattr(tab, 'notify', MagicMock())

        # Mock UI
        mock_table = MagicMock(spec=DataTable)
        mock_status = MagicMock(spec=Label)
        setattr(tab, 'query_one', MagicMock(side_effect=lambda selector, type=None: {
            "#deps-table": mock_table,
            "#deps-status": mock_status
        }.get(selector)))

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

        # Verify table update
        # Should now have "Outdated" status (formatted)
        add_row_calls = mock_table.add_row.call_args_list
        self.assertTrue(len(add_row_calls) > 0)
        # Check that status is red/outdated
        self.assertIn("Outdated", str(add_row_calls[0][0]))


if __name__ == "__main__":
    unittest.main()
