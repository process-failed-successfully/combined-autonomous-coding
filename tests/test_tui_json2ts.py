import pytest
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Input

# Use module-level skip if textual isn't available
pytest.importorskip("textual")

from shared.tui_json2ts import Json2TsTab

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield Json2TsTab()

@pytest.mark.asyncio
async def test_tui_json2ts():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Check initial state
        root_name_input = app.query_one("#root-name-input", Input)
        assert root_name_input.value == "Root"

        json_input = app.query_one("#json2ts-input", TextArea)
        ts_output = app.query_one("#json2ts-output", TextArea)
        assert ts_output.text == ""

        # Input some JSON
        test_json = '{"a": 1, "b": "str"}'
        json_input.text = test_json

        # Give UI a moment to process the reactive change
        await pilot.pause()

        # Check output
        expected_output = """export interface Root {
  a: number;
  b: string;
}"""
        assert expected_output in ts_output.text

        # Change root name
        root_name_input.value = "MyType"
        await pilot.pause()

        expected_output_2 = """export interface MyType {
  a: number;
  b: string;
}"""
        assert expected_output_2 in ts_output.text

        # Clear input
        json_input.text = "   "
        await pilot.pause()
        assert ts_output.text == ""
