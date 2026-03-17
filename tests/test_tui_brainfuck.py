import pytest
from textual.app import App
from shared.tui_brainfuck import BrainfuckLabTab

class DummyApp(App):
    def compose(self):
        yield BrainfuckLabTab()

@pytest.mark.asyncio
async def test_tui_brainfuck_compose():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Check that the tab renders and input areas exist
        assert app.query_one("#bf-code-input") is not None
        assert app.query_one("#bf-input-data") is not None
        assert app.query_one("#bf-output-log") is not None
        assert app.query_one("#btn-bf-load") is not None
        assert app.query_one("#btn-bf-step") is not None
        assert app.query_one("#btn-bf-run") is not None
        assert app.query_one("#btn-bf-reset") is not None
