import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog
from shared.tui_env import EnvTab

class EnvTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield EnvTab(self.project_dir)

class TestEnvTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = EnvTestApp(self.project_dir)

    @patch("shared.tui_env.EnvManager")
    async def test_env_status_missing(self, MockEnvManager):
        # Setup Mock for missing files
        mock_instance = MockEnvManager.return_value
        mock_instance.env_path.exists.return_value = False
        mock_instance.example_path.exists.return_value = False
        mock_instance.check.return_value = (False, [], ["No .env.example found"])
        # Mock _parse_env to return empty dicts (accessed directly in TUI)
        mock_instance._parse_env.side_effect = lambda p: {}

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(EnvTab)

            # Verify status label
            lbl = tab.query_one("#lbl-env-status")
            self.assertIn("Files missing", str(lbl.render()))

            # Verify Init button enabled
            btn_init = tab.query_one("#btn-env-init", Button)
            self.assertFalse(btn_init.disabled)

            # Click Init
            mock_instance.init.return_value = (True, "Initialized files")
            await pilot.click("#btn-env-init")

            mock_instance.init.assert_called_once()

    @patch("shared.tui_env.EnvManager")
    async def test_env_sync_status(self, MockEnvManager):
        # Setup Mock for out of sync
        mock_instance = MockEnvManager.return_value
        mock_instance.env_path.exists.return_value = True
        mock_instance.example_path.exists.return_value = True
        mock_instance.check.return_value = (False, ["MISSING_KEY"], [])

        # Mock _parse_env
        def parse_side_effect(path):
            if path == mock_instance.env_path:
                return {"API_KEY": "123"}
            else:
                return {"API_KEY": "", "MISSING_KEY": ""}
        mock_instance._parse_env.side_effect = parse_side_effect

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(EnvTab)

            # Verify status label
            lbl = tab.query_one("#lbl-env-status")
            self.assertIn("Out of Sync", str(lbl.render()))

            # Verify Sync button enabled
            btn_sync = tab.query_one("#btn-env-sync", Button)
            self.assertFalse(btn_sync.disabled)

            # Check Table Content
            table = tab.query_one("#env-table", DataTable)
            # Should have 2 rows
            self.assertEqual(table.row_count, 2)

            # Row 0: API_KEY (Present, Present)
            # Row 1: MISSING_KEY (Missing, Present) - sorted alphabetically

            # Click Sync
            mock_instance.sync.return_value = (True, "Synced keys")
            await pilot.click("#btn-env-sync")

            mock_instance.sync.assert_called_once()

    @patch("shared.tui_env.EnvManager")
    async def test_generate_secret(self, MockEnvManager):
        mock_instance = MockEnvManager.return_value
        mock_instance.env_path.exists.return_value = True
        mock_instance.example_path.exists.return_value = True
        mock_instance.check.return_value = (True, [], [])
        mock_instance._parse_env.return_value = {}

        async with self.app.run_test(size=(120, 40)) as pilot:
            # Input Key
            self.app.query_one("#inp-env-key").value = "NEW_SECRET"

            # Focus and Press
            self.app.query_one("#btn-env-generate").focus()
            await pilot.press("enter")
            await pilot.pause()

            mock_instance.generate_secret.assert_called_with("NEW_SECRET")

if __name__ == "__main__":
    unittest.main()
