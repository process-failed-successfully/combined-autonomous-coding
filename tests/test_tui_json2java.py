import pytest
from unittest.mock import patch, MagicMock
try:
    from textual.app import App
    from textual.widgets import TabbedContent, TextArea, Input, Button
    from shared.tui_json2java import Json2JavaTab
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual not available")
@pytest.mark.asyncio
async def test_json2java_tab():
    class TestApp(App):
        def compose(self):
            with TabbedContent():
                yield Json2JavaTab()

    app = TestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2JavaTab)
        assert tab is not None

        # Test conversion
        input_area = app.query_one("#j2j-input", TextArea)
        input_area.text = '{"name": "Test"}'

        tab.action_convert()
        await pilot.pause()

        output_area = app.query_one("#j2j-output", TextArea)
        assert "public class RootObject" in output_area.text
        assert "private String name;" in output_area.text

        # Test empty input
        input_area.text = ''
        tab.action_convert()
        await pilot.pause()
        assert "Please enter JSON data" in output_area.text

        # Test invalid input
        input_area.text = '{"name": "Test"'
        tab.action_convert()
        await pilot.pause()
        assert "Error: Invalid JSON" in output_area.text

        # Test clear
        input_area.text = '{"name": "Test"}'
        tab.action_clear()
        await pilot.pause()
        assert input_area.text == ""
        assert output_area.text == ""
