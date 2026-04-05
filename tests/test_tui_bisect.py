import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from textual.widgets import Button, Input, RichLog, Select, Markdown
from textual.app import App, ComposeResult
from pathlib import Path
from shared.tui_bisect import BisectTab

class BisectTestApp(App):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def compose(self) -> ComposeResult:
        yield self.tab

class TestBisectTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")

        # Patch get_git_log
        self.patcher_log = patch("shared.tui_bisect.get_git_log")
        self.mock_get_log = self.patcher_log.start()
        self.mock_get_log.return_value = [
            {"hash": "abc1234", "message": "fix: bug", "date": "2023-01-02"},
            {"hash": "def5678", "message": "feat: new thing", "date": "2023-01-01"}
        ]

        # Patch analyze_commit
        self.patcher_analyze = patch("shared.tui_bisect.analyze_commit", new_callable=AsyncMock)
        self.mock_analyze = self.patcher_analyze.start()
        self.mock_analyze.return_value = "## Analysis\nCulprit identified."

        # Patch asyncio.create_subprocess_exec
        self.patcher_subprocess = patch("asyncio.create_subprocess_exec", new_callable=AsyncMock)
        self.mock_subprocess = self.patcher_subprocess.start()

    async def asyncTearDown(self):
        self.patcher_log.stop()
        self.patcher_analyze.stop()
        self.patcher_subprocess.stop()

    async def test_mount_and_load(self):
        tab = BisectTab(self.project_dir)
        app = BisectTestApp(tab)
        async with app.run_test() as pilot:
            # Verify commits loaded into select
            select = app.query_one("#bisect-good-select", Select)
            # Textual Select options might include internal state or blank.
            # We check if our expected values are present in the options list (list of tuples or objects)
            # Select._options is internal, assume public API usage if possible, but for testing internals is ok.

            # Check if we have at least our options
            options = select._options
            # Filter out any 'Select.BLANK' if present (it's usually a unique object)
            real_options = [opt for opt in options if isinstance(opt, tuple) and len(opt) == 2]

            self.assertTrue(len(real_options) >= 2)
            # Check content
            hashes = [opt[1] for opt in real_options]
            self.assertIn("abc1234", hashes)
            self.assertIn("def5678", hashes)

    async def test_start_bisect_flow(self):
        # Setup mock process
        mock_process = MagicMock()
        mock_process.stdout.readline = AsyncMock(side_effect=[
            b"Bisecting: 6 revisions left to test after this (roughly 3 steps)\n",
            b"[abc1234] Some commit message\n",
            b"abc1234 is the first bad commit\n",
            b""
        ])
        mock_process.wait = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b"")) # For start/reset calls

        self.mock_subprocess.return_value = mock_process

        tab = BisectTab(self.project_dir)
        app = BisectTestApp(tab)

        async with app.run_test() as pilot:
            # Set inputs
            app.query_one("#bisect-bad", Input).value = "HEAD"
            # Use manual input instead of select
            app.query_one("#bisect-good-manual", Input).value = "def5678"
            app.query_one("#bisect-command", Input).value = "pytest"

            # Click Start
            app.query_one("#btn-bisect-start").press()
        await pilot.pause()

            # Wait for worker to finish
            # app.workers.wait_for_complete() is available in newer textual
            # otherwise just pause enough
            await pilot.pause(0.5)
            await app.workers.wait_for_complete()

            # Verify git calls
            calls = self.mock_subprocess.call_args_list
            self.assertTrue(len(calls) >= 3)

            # Check for start command
            start_call = next((c for c in calls if "start" in c[0]), None)
            self.assertIsNotNone(start_call)

            # Check for run command
            run_call = next((c for c in calls if "run" in c[0]), None)
            self.assertIsNotNone(run_call)

            # Verify Analysis was triggered
            self.mock_analyze.assert_awaited()
            args, _ = self.mock_analyze.call_args
            self.assertEqual(args[1], "abc1234") # Culprit hash

    async def test_reset_bisect(self):
        mock_process = MagicMock()
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        self.mock_subprocess.return_value = mock_process

        tab = BisectTab(self.project_dir)
        app = BisectTestApp(tab)
        async with app.run_test() as pilot:
            app.query_one("#btn-bisect-reset").press()
        await pilot.pause()
            await pilot.pause(0.1)

            # Verify reset call
            calls = self.mock_subprocess.call_args_list
            reset_call = next((c for c in calls if "reset" in c[0]), None)
            self.assertIsNotNone(reset_call)
