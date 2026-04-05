import asyncio
import tempfile
from pathlib import Path
import pytest
from textual.app import App, ComposeResult
from shared.tui_log_tail import LogTailTab

class LogTailApp(App):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield LogTailTab(self.project_dir)

@pytest.mark.asyncio
async def test_log_tail_polling():
    # Create a temp dir and file
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        log_file = project_dir / "test.log"
        initial_content = "Line 1\n"
        log_file.write_text(initial_content, encoding="utf-8")

        app = LogTailApp(project_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            tab = app.query_one(LogTailTab)

            # Simulate file selection
            tab.current_file = log_file
            tab.query_one("#btn-tail-start").disabled = False

            # Start tailing
            pilot.app.query_one("#btn-tail-start").press()
            await pilot.pause()
            assert tab.is_tailing

            # Verify file position updated (read initial content)
            # In text mode with utf-8, tell() returns byte offset equivalent
            assert tab.file_pos >= len(initial_content.encode('utf-8'))

            # Append content
            new_content = "Line 2\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(new_content)

            # Manually trigger poll to avoid waiting for timer
            tab.read_new_lines()

            # Verify position advanced
            expected_pos = len((initial_content + new_content).encode('utf-8'))
            assert tab.file_pos >= expected_pos

            # Stop tailing
            pilot.app.query_one("#btn-tail-stop").press()
            await pilot.pause()
            assert not tab.is_tailing
            assert tab.tail_timer is None
