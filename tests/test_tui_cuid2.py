import pytest

from shared.cuid2_lab import HAS_CUID2

pytestmark = pytest.mark.skipif(not HAS_CUID2, reason="cuid2 library not installed")

# Try to import textual stuff
try:
    from textual.widgets import Input, Button, Static
    from textual.app import App, ComposeResult
    from textual.widgets import TabbedContent, TabPane
    from shared.tui_cuid2 import Cuid2LabTab
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

if TEXTUAL_AVAILABLE:
    class Cuid2LabApp(App):
        def compose(self) -> ComposeResult:
            with TabbedContent():
                with TabPane("CUID2 Lab", id="tab-cuid2"):
                    yield Cuid2LabTab()

    @pytest.mark.asyncio
    async def test_cuid2_tui_generate():
        app = Cuid2LabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Set values
            length_input = app.query_one("#cuid2-length", Input)
            length_input.value = "15"
            count_input = app.query_one("#cuid2-count", Input)
            count_input.value = "3"

            await pilot.pause()

            # Click generate
            await pilot.click("#btn-cuid2-generate")
            await pilot.pause()

            # Check output
            output = app.query_one("#cuid2-output", Static)
            text = output.render()
            assert "Generated CUID2(s):" in str(text)

            # It should contain 3 generated items, each wrapped in bold green formatting
            # which makes the length harder to assert directly on the string, but we can verify line count
            lines = str(text).split("\n")
            assert len(lines) >= 4 # Header + 3 CUID2s

    @pytest.mark.asyncio
    async def test_cuid2_tui_invalid_input():
        app = Cuid2LabApp()
        async with app.run_test() as pilot:
            await pilot.pause()

            # Set invalid count
            count_input = app.query_one("#cuid2-count", Input)
            count_input.value = "-5"

            await pilot.click("#btn-cuid2-generate")
            await pilot.pause()

            output = app.query_one("#cuid2-output", Static)
            assert "Error: Count must be greater than 0." in str(output.render())
