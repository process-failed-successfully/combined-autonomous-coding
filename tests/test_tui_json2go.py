import pytest
from unittest.mock import MagicMock

pytest.importorskip("textual")

from textual.app import App, ComposeResult
from textual.widgets import TabbedContent, TabPane
from shared.tui_json2go import Json2GoLabTab

class Json2GoLabApp(App):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("JSON to Go", id="tab-json2go"):
                yield Json2GoLabTab()

@pytest.mark.asyncio
async def test_json2go_tab_convert_success():
    app = Json2GoLabApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2GoLabTab)
        input_ta = tab.query_one("#json2go-input-ta")
        output_ta = tab.query_one("#json2go-output-ta")

        # Set input
        input_ta.text = '{"name": "test", "id": 123}'

        # Trigger convert action
        await tab.action_convert()
        await pilot.pause()

        # Verify output
        assert "type RootStruct struct" in output_ta.text
        assert "Name string" in output_ta.text
        assert "Id int" in output_ta.text

@pytest.mark.asyncio
async def test_json2go_tab_convert_error():
    app = Json2GoLabApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2GoLabTab)
        input_ta = tab.query_one("#json2go-input-ta")
        output_ta = tab.query_one("#json2go-output-ta")
        status = tab.query_one("#json2go-status")

        # Set invalid input
        input_ta.text = '{"name": "test", '

        # Trigger convert action
        await tab.action_convert()
        await pilot.pause()

        # Verify output and status
        assert output_ta.text == ""
        assert "Invalid JSON" in str(status.renderable)

@pytest.mark.asyncio
async def test_json2go_tab_empty_input():
    app = Json2GoLabApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2GoLabTab)
        input_ta = tab.query_one("#json2go-input-ta")
        output_ta = tab.query_one("#json2go-output-ta")
        status = tab.query_one("#json2go-status")

        # Ensure empty
        input_ta.text = ""

        # Trigger convert action
        await tab.action_convert()
        await pilot.pause()

        # Verify output and status
        assert output_ta.text == ""
        assert "Input JSON is empty" in str(status.renderable)
