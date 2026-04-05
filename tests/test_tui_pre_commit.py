import unittest
import shutil
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from shared.tui_pre_commit import PreCommitLabTab

class PreCommitApp(App):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield PreCommitLabTab(self.project_dir)

class TestPreCommitTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/mock/project")

    @patch("shared.pre_commit_lab.PreCommitLabManager.is_installed")
    @patch("shared.pre_commit_lab.PreCommitLabManager.config_exists")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_hooks")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_config_content")
    async def test_tui_mount(self, mock_get_content, mock_get_hooks, mock_config_exists, mock_is_installed):
        mock_is_installed.return_value = True
        mock_config_exists.return_value = True
        mock_get_hooks.return_value = [{"id": "test", "repo": "local", "rev": "v1"}]
        mock_get_content.return_value = "config: content"

        app = PreCommitApp(self.project_dir)
        async with app.run_test() as pilot:
            tab = app.query_one(PreCommitLabTab)

            # Check status labels
            self.assertIn("Installed", str(tab.query_one("#pc-tool-status").renderable))
            self.assertIn("Found", str(tab.query_one("#pc-config-status").renderable))

            # Check table
            table = tab.query_one("#pc-hooks-table")
            self.assertEqual(table.row_count, 1)

    @patch("shared.pre_commit_lab.PreCommitLabManager.is_installed")
    @patch("shared.pre_commit_lab.PreCommitLabManager.config_exists")
    @patch("shared.pre_commit_lab.PreCommitLabManager.create_default_config")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_config_content")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_hooks")
    async def test_create_config(self, mock_get_hooks, mock_get_content, mock_create, mock_config_exists, mock_is_installed):
        mock_is_installed.return_value = True
        mock_config_exists.side_effect = [False, True] # First check false, then true after creation
        mock_create.return_value = True
        mock_get_content.return_value = "new config"
        mock_get_hooks.return_value = []

        app = PreCommitApp(self.project_dir)
        async with app.run_test() as pilot:
            # Click create config button
            app.query_one("#btn-pc-create-config").press()
        await pilot.pause()

            # Verify manager called
            mock_create.assert_called_once()

    @patch("shared.pre_commit_lab.PreCommitLabManager.is_installed")
    @patch("shared.pre_commit_lab.PreCommitLabManager.config_exists")
    @patch("shared.pre_commit_lab.PreCommitLabManager.run_all_hooks")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_config_content")
    @patch("shared.pre_commit_lab.PreCommitLabManager.get_hooks")
    async def test_run_hooks(self, mock_get_hooks, mock_get_content, mock_run, mock_config_exists, mock_is_installed):
        mock_is_installed.return_value = True
        mock_config_exists.return_value = True
        mock_run.return_value = (True, "Hook output")
        mock_get_content.return_value = "config"
        mock_get_hooks.return_value = []

        app = PreCommitApp(self.project_dir)
        async with app.run_test() as pilot:
            app.query_one("#btn-pc-run-all").press()
        await pilot.pause()

            mock_run.assert_called_once()

if __name__ == "__main__":
    unittest.main()
