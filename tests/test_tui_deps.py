import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure shared can be imported
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui import DependenciesTab

class TestTUIDependencies(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = DependenciesTab(self.project_dir)

        # Mock external dependencies
        self.tab.analyzer = MagicMock()
        self.tab.updater = MagicMock()

        # Mock UI methods
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    def test_load_deps(self):
        # Mock data
        self.tab.analyzer.scan.return_value = {
            "python": [
                {
                    "source": "requirements.txt",
                    "dependencies": [
                        {"name": "flask", "version": "2.0.0", "type": "prod"}
                    ]
                }
            ]
        }

        # Mock Tree widget
        mock_tree = MagicMock()
        mock_root = MagicMock()
        mock_tree.root = mock_root

        # Mock query_one to return our mock tree
        self.tab.query_one.return_value = mock_tree

        # Run
        self.tab.load_deps()

        # Verify scan was called
        self.tab.analyzer.scan.assert_called_once()

        # Verify tree population
        # Should add Python node
        mock_root.add.assert_called()
        args, _ = mock_root.add.call_args
        self.assertIn("Python", args[0])

    def test_on_dep_selected(self):
        # Mock UI elements
        mock_log = MagicMock()
        mock_btn = MagicMock()

        def query_side_effect(selector, type=None):
            if selector == "#dep-details-log":
                return mock_log
            if selector == "#btn-dep-update":
                return mock_btn
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Create mock event
        mock_node = MagicMock()
        mock_node.data = {
            "name": "flask",
            "version": "2.0.0",
            "latest": "2.1.0",
            "outdated": True,
            "type": "prod",
            "source": "requirements.txt",
            "lang": "python"
        }
        mock_event = MagicMock()
        mock_event.node = mock_node

        # Run
        self.tab.on_dep_selected(mock_event)

        # Verify details updated
        mock_log.clear.assert_called()
        mock_log.write.assert_called()

        # Verify update button enabled
        self.assertEqual(mock_btn.disabled, False)

        # Verify stored selection
        self.assertEqual(self.tab.selected_dep, mock_node.data)

    async def test_update_package(self):
        # Mock updater
        self.tab.updater.update_dependency.return_value = True

        # Mock UI elements
        mock_btn = MagicMock()
        mock_log = MagicMock()

        def query_side_effect(selector, type=None):
            if selector == "#btn-dep-update":
                return mock_btn
            if selector == "#dep-details-log":
                return mock_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        dep_data = {
            "name": "flask",
            "version": "2.0.0",
            "latest": "2.1.0",
            "type": "prod",
            "source": "requirements.txt"
        }

        # Run
        await self.tab.update_package(dep_data)

        # Verify update called
        self.tab.updater.update_dependency.assert_called_with(
            self.project_dir / "requirements.txt",
            "flask",
            "2.1.0",
            "prod"
        )

        # Verify success notification
        self.tab.notify.assert_called_with("Successfully updated flask.", severity="information")

        # Verify UI update
        self.assertEqual(mock_btn.disabled, True)

    async def test_check_updates(self):
        # Mock analyzer
        self.tab.analyzer.check_updates.return_value = {"python": []}

        # Mock UI
        mock_tree = MagicMock()
        mock_tree.root = MagicMock()
        self.tab.query_one.return_value = mock_tree

        # Run
        await self.tab.check_updates()

        # Verify check_updates called
        self.tab.analyzer.check_updates.assert_called()

        # Verify load_deps called (implied by tree usage)
        mock_tree.clear.assert_called()

if __name__ == "__main__":
    unittest.main()
