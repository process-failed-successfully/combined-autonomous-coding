import pytest
import sys
from pathlib import Path
import asyncio

# Ensure shared modules can be imported
sys.path.insert(0, str(Path(__file__).parents[1]))

pytest.importorskip("textual")
from shared.tui_fuzz import FuzzLabTab
from textual.widgets import Input, Button, RichLog
from textual.app import App, ComposeResult

class FuzzTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield FuzzLabTab(project_dir=self.project_dir)

@pytest.mark.asyncio
async def test_tui_fuzz_cli(tmp_path):
    app = FuzzTestApp(project_dir=tmp_path)

    # Mock fuzz_cli so we don't actually run commands
    from unittest.mock import patch
    with patch("shared.fuzz_lab.FuzzLabManager.fuzz_cli") as mock_fuzz:
        mock_fuzz.return_value = [
            {"iteration": 1, "type": "Error", "input_preview": "bad input", "return_code": 1}
        ]

        async with app.run_test() as pilot:
            # Wait for tab to load
            await pilot.pause()

            # Switch to CLI pane (though it's default)
            app.query_one("#fuzz-cli-pane").press()
        await pilot.pause()
            await pilot.pause()

            # Find and set inputs programmatically to avoid flaky press()
            app.query_one("#fuzz-cli-target", Input).value = "echo hello"
            app.query_one("#fuzz-cli-count", Input).value = "2"

            # Click fuzz button
            app.query_one("#btn-fuzz-cli").press()
        await pilot.pause()

            # Wait for fuzzing thread (we use asyncio.to_thread in FuzzLabTab)
            # We can pause a bit longer to allow the thread to finish
            await asyncio.sleep(0.1)
            await pilot.pause()

            mock_fuzz.assert_called_once_with("echo hello", count=2, timeout=5)

            # Verify log output
            log = app.query_one("#fuzz-cli-log", RichLog)
            log_lines = "\n".join([line.text for line in log.lines])
            assert "Starting CLI fuzzing for 'echo hello'" in log_lines
            assert "Found 1 issues." in log_lines

@pytest.mark.asyncio
async def test_tui_fuzz_func(tmp_path):
    app = FuzzTestApp(project_dir=tmp_path)

    # Mock fuzz_function so we don't actually run commands
    from unittest.mock import patch
    with patch("shared.fuzz_lab.FuzzLabManager.fuzz_function") as mock_fuzz:
        mock_fuzz.return_value = [
            {"iteration": 1, "type": "ValueError", "args": "[1]", "kwargs": "{}", "error": "Bad val"}
        ]

        async with app.run_test() as pilot:
            # Wait for tab to load
            await pilot.pause()

            # Target the func pane directly and interact with it
            # To click it, we click the tab label, but Textual testing allows direct clicking
            tabbed_content = app.query_one("TabbedContent")
            tabbed_content.active = "fuzz-func-pane"
            await pilot.pause()

            # Focus on input and set value
            app.query_one("#fuzz-func-target", Input).value = "test.py:my_func"
            app.query_one("#fuzz-func-count", Input).value = "3"

            # Click fuzz button
            app.query_one("#btn-fuzz-func").press()
        await pilot.pause()

            await asyncio.sleep(0.1)
            await pilot.pause()

            mock_fuzz.assert_called_once_with("test.py", "my_func", count=3)

            # Verify log output
            log = app.query_one("#fuzz-func-log", RichLog)
            log_lines = "\n".join([line.text for line in log.lines])
            assert "Starting function fuzzing for 'my_func' in 'test.py'" in log_lines
            assert "Found 1 exceptions." in log_lines
