import pytest
import os
import sys

try:
    from textual.app import App
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = object

if TEXTUAL_AVAILABLE:
    from shared.tui_ini2json import Ini2JsonLabTab

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is required")
class DummyApp(App):
    def compose(self):
        yield Ini2JsonLabTab()

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is required")
@pytest.mark.asyncio
async def test_ini2json_tui_basic():
    app = DummyApp()
    async with app.run_test(headless=True) as pilot:
        # Check initial state
        input_area = app.query_one("#ini2json-input")
        output_area = app.query_one("#ini2json-output")
        assert input_area.text == ""
        assert output_area.text == ""

        # Input INI
        input_area.text = "[Section]\nkey=value"

        # Click convert
        await pilot.click("#btn-convert-ini2json")
        await pilot.pause(0.1)

        # Output should contain the converted JSON
        assert '"Section"' in output_area.text
        assert '"key"' in output_area.text
        assert '"value"' in output_area.text

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is required")
@pytest.mark.asyncio
async def test_ini2json_tui_invalid():
    app = DummyApp()
    async with app.run_test(headless=True) as pilot:
        input_area = app.query_one("#ini2json-input")
        output_area = app.query_one("#ini2json-output")

        # Input Invalid INI
        input_area.text = "[Section\nbad_format"

        # Click convert
        await pilot.click("#btn-convert-ini2json")
        await pilot.pause(0.1)

        # Output should display error message
        assert "Error:" in output_area.text
