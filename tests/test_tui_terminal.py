import unittest
from unittest.mock import MagicMock, patch, AsyncMock, ANY
from pathlib import Path
import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Input, RichLog
from shared.tui_terminal import TerminalTab, HistoryInput

class TerminalTestApp(App[None]):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield TerminalTab(self.project_dir)

class TestTerminalTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project").resolve()
        # Ensure dir exists for real path resolution if needed, though we mock subprocess
        # For cd logic, we might need real paths or mock Path.
        # But Path(..).resolve() works on filesystem.
        # Let's use current dir for safety
        self.project_dir = Path.cwd()
        self.app = TerminalTestApp(self.project_dir)

    async def test_history_input(self):
        """Test HistoryInput up/down navigation."""
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(TerminalTab)
            inp = tab.query_one("#terminal-input", HistoryInput)

            inp.add_to_history("cmd1")
            inp.add_to_history("cmd2")

            # Initial state
            self.assertEqual(inp.history, ["cmd1", "cmd2"])

            # Up (cmd2)
            inp.action_history_up()
            self.assertEqual(inp.value, "cmd2")

            # Up (cmd1)
            inp.action_history_up()
            self.assertEqual(inp.value, "cmd1")

            # Down (cmd2)
            inp.action_history_down()
            self.assertEqual(inp.value, "cmd2")

            # Down (empty/current)
            inp.action_history_down()
            self.assertEqual(inp.value, "")

    @patch("asyncio.create_subprocess_shell")
    async def test_run_command(self, mock_subprocess):
        # Mock process
        mock_process = AsyncMock()
        mock_process.stdout.readline.side_effect = [
            b"output line 1\n",
            b"output line 2\n",
            b""
        ]
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(TerminalTab)
            inp = tab.query_one("#terminal-input", Input)

            # Type command
            inp.value = "ls -la"
            await inp.action_submit()
            await pilot.pause(0.5) # Wait for async execution

            # Verify subprocess called
            mock_subprocess.assert_called_with(
                "ls -la",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=self.project_dir,
                env=ANY
            )

            # Verify log output
            log = tab.query_one("#terminal-log", RichLog)
            # RichLog stores Strips
            self.assertTrue(len(log.lines) >= 3)

    async def test_cd_command(self):
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(TerminalTab)
            inp = tab.query_one("#terminal-input", Input)

            # Initial CWD
            self.assertEqual(tab.cwd, self.project_dir)

            # Type cd ..
            inp.value = "cd .."
            await inp.action_submit()
            await pilot.pause(0.5)

            # Verify CWD changed
            self.assertEqual(tab.cwd, self.project_dir.parent)

    async def test_cd_invalid(self):
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(TerminalTab)
            inp = tab.query_one("#terminal-input", Input)

            current_cwd = tab.cwd

            # Type invalid cd
            inp.value = "cd /non/existent/path"
            await inp.action_submit()
            await pilot.pause(0.5)

            # Verify CWD NOT changed
            self.assertEqual(tab.cwd, current_cwd)

            # Verify error logged
            log = tab.query_one("#terminal-log", RichLog)
            self.assertTrue(len(log.lines) > 0)

if __name__ == "__main__":
    unittest.main()
