import pytest

try:
    from textual.app import App, ComposeResult
    from textual.widgets import TabbedContent, TabPane
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

if TEXTUAL_AVAILABLE:
    from shared.tui_json2java import Json2JavaLabTab
    from textual.widgets import TextArea, Input, Static


@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual not installed")
@pytest.mark.asyncio
async def test_tui_json2java_basic():
    class TestApp(App):
        def compose(self) -> ComposeResult:
            with TabbedContent():
                with TabPane("JSON to Java", id="tab-json2java"):
                    yield Json2JavaLabTab()

    app = TestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2JavaLabTab)
        input_ta = tab.query_one("#json2java-input-ta", TextArea)
        output_ta = tab.query_one("#json2java-output-ta", TextArea)
        name_input = tab.query_one("#json2java-name-input", Input)
        package_input = tab.query_one("#json2java-package-input", Input)
        status = tab.query_one("#json2java-status", Static)

        # Test empty input
        await tab.action_convert()
        await pilot.pause()
        assert "Input JSON is empty" in status.renderable

        # Test invalid JSON
        input_ta.text = "{"
        await tab.action_convert()
        await pilot.pause()
        assert "Invalid JSON" in status.renderable

        # Test valid JSON
        input_ta.text = '{"name": "test"}'
        name_input.value = "MyRoot"
        package_input.value = "com.test"
        await tab.action_convert()
        await pilot.pause()

        assert "Conversion successful" in status.renderable
        assert "package com.test;" in output_ta.text
        assert "public class MyRoot {" in output_ta.text
        assert "private String name;" in output_ta.text
