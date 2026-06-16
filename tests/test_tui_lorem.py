import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input, Select, Switch, Button, Static
from shared.tui_lorem import LoremLabTab
from unittest.mock import patch, MagicMock

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield LoremLabTab()

@pytest.mark.asyncio
async def test_lorem_lab_tab_render():
    app = DummyApp()
    async with app.run_test() as pilot:
        tab = app.query_one(LoremLabTab)
        assert tab is not None

        # Test default states
        assert app.query_one("#input-lorem-count", Input).value == "1"
        assert app.query_one("#select-lorem-type", Select).value == "paragraphs"
        assert app.query_one("#switch-lorem-start", Switch).value is True
        assert str(app.query_one("#static-lorem-output", Static).render()) == ""

@pytest.mark.asyncio
async def test_lorem_lab_generate_button():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Click generate
        pilot.app.query_one("#btn-generate-lorem").press()
        await pilot.pause()

        # Output should no longer be empty
        output_static = app.query_one("#static-lorem-output", Static)
        assert "Lorem ipsum dolor sit amet" in str(output_static.render())

@pytest.mark.asyncio
async def test_lorem_lab_copy_button():
    app = DummyApp()
    app.notify = MagicMock()

    with patch("pyperclip.copy") as mock_copy:
        async with app.run_test() as pilot:
            # First generate
            pilot.app.query_one("#btn-generate-lorem").press()
            await pilot.pause()

            # Then copy
            pilot.app.query_one("#btn-copy-lorem").press()
            await pilot.pause()

            # Assert copy was called
            assert mock_copy.called

            # Assert notify was called
            app.notify.assert_called_with("Copied to clipboard!", title="Success")
