import pytest
from textual.widgets import TextArea, Input, Static
from shared.tui_json2ts import Json2TsLabTab
from textual.app import App, ComposeResult
from textual.widgets import TabbedContent, TabPane

class DummyApp(App):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("JSON to TS", id="tab-json2ts"):
                yield Json2TsLabTab()

@pytest.mark.asyncio
async def test_json2ts_tab():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Give it a moment to render
        await pilot.pause()

        # Find the text areas and inputs
        input_ta = app.query_one("#json2ts-input-ta", TextArea)
        output_ta = app.query_one("#json2ts-output-ta", TextArea)
        name_input = app.query_one("#json2ts-name-input", Input)
        status = app.query_one("#json2ts-status", Static)

        # Test 1: Empty conversion
        tab = app.query_one(Json2TsLabTab)
        await tab.action_convert()
        await pilot.pause()
        assert "Input JSON is empty" in status.renderable

        # Test 2: Valid conversion
        input_ta.text = '{"name": "Alice"}'
        name_input.value = "User"

        await tab.action_convert()
        await pilot.pause()

        assert "export interface User" in output_ta.text
        assert "name: string;" in output_ta.text
        assert "Conversion successful" in status.renderable

        # Test 3: Invalid JSON
        input_ta.text = '{"name": "Alice"'

        await tab.action_convert()
        await pilot.pause()

        assert "Invalid JSON" in status.renderable
