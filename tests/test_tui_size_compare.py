import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
pytest.importorskip("textual")

from shared.tui_size_compare import SizeCompareTab
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button
from unittest.mock import patch

class SizeCompareTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir
        self.notifications = []

    def compose(self) -> ComposeResult:
        yield SizeCompareTab(project_dir=self.project_dir)

    def notify(self, message: str, title: str = "", severity: str = "information", timeout: float = 3.0) -> None:
        self.notifications.append((message, severity))

@pytest.mark.asyncio
async def test_size_compare_tui_success(tmp_path):
    app = SizeCompareTestApp(project_dir=tmp_path)

    with patch("shared.size_compare_lab.SizeCompareManager.compare_sizes") as mock_compare:
        mock_compare.return_value = "Format          | Size (bytes)\nJSON            | 12"

        async with app.run_test() as pilot:
            await pilot.pause()

            # Find input and put some text
            input_text = app.query_one("#size-cmp-input", TextArea)
            input_text.text = '{"a": 1}'

            # Click button
            await pilot.click("#btn-size-compare")
            await pilot.pause()

            mock_compare.assert_called_once_with('{"a": 1}')

            # Verify output
            out = app.query_one("#size-cmp-output", TextArea)
            assert "JSON            | 12" in out.text

            # Verify notification
            assert any(msg == "Comparison complete." for msg, _ in app.notifications)

@pytest.mark.asyncio
async def test_size_compare_tui_empty_input(tmp_path):
    app = SizeCompareTestApp(project_dir=tmp_path)

    async with app.run_test() as pilot:
        await pilot.pause()

        # Clear input text
        input_text = app.query_one("#size-cmp-input", TextArea)
        input_text.text = ""

        # Click button
        await pilot.click("#btn-size-compare")
        await pilot.pause()

        # Output should be empty
        out = app.query_one("#size-cmp-output", TextArea)
        assert out.text == ""

        # Verify notification
        assert any(msg == "Input required." and sev == "error" for msg, sev in app.notifications)

@pytest.mark.asyncio
async def test_size_compare_tui_exception(tmp_path):
    app = SizeCompareTestApp(project_dir=tmp_path)

    with patch("shared.size_compare_lab.SizeCompareManager.compare_sizes") as mock_compare:
        mock_compare.side_effect = ValueError("Some weird failure")

        async with app.run_test() as pilot:
            await pilot.pause()

            input_text = app.query_one("#size-cmp-input", TextArea)
            input_text.text = '{"a": 1}'

            # Click button
            await pilot.click("#btn-size-compare")
            await pilot.pause()

            # Verify output contains error
            out = app.query_one("#size-cmp-output", TextArea)
            assert "Error: Some weird failure" in out.text

            # Verify notification
            assert any("Error: Some weird failure" in msg and sev == "error" for msg, sev in app.notifications)
