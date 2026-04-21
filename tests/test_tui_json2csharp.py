import pytest
from textual.widgets import TextArea, Input, Static
import textual

# Check if textual is available for TUI tests
try:
    import textual
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

if TEXTUAL_AVAILABLE:
    from textual.app import App
    from shared.tui_json2csharp import Json2CSharpTab

    class Json2CSharpTestApp(App):
        def compose(self):
            yield Json2CSharpTab()

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is not available")
@pytest.mark.asyncio
async def test_tui_json2csharp_convert():
    app = Json2CSharpTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2CSharpTab)

        # Set input data
        input_ta = tab.query_one("#json2csharp-input-ta", TextArea)
        input_ta.text = '{"name": "test"}'

        # Trigger conversion
        await tab.action_convert()
        await pilot.pause(0.1)

        output_ta = tab.query_one("#json2csharp-output-ta", TextArea)
        status = tab.query_one("#json2csharp-status", Static)

        assert "public class RootClass" in output_ta.text
        assert "public string Name { get; set; }" in output_ta.text
        assert "Conversion successful." in str(status.render())

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is not available")
@pytest.mark.asyncio
async def test_tui_json2csharp_invalid_json():
    app = Json2CSharpTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2CSharpTab)

        input_ta = tab.query_one("#json2csharp-input-ta", TextArea)
        input_ta.text = '{invalid}'

        await tab.action_convert()
        await pilot.pause(0.1)

        output_ta = tab.query_one("#json2csharp-output-ta", TextArea)
        status = tab.query_one("#json2csharp-status", Static)

        assert output_ta.text == ""
        assert "Invalid JSON" in str(status.render())

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="Textual is not available")
@pytest.mark.asyncio
async def test_tui_json2csharp_empty_input():
    app = Json2CSharpTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Json2CSharpTab)

        await tab.action_convert()
        await pilot.pause(0.1)

        output_ta = tab.query_one("#json2csharp-output-ta", TextArea)
        status = tab.query_one("#json2csharp-status", Static)

        assert output_ta.text == ""
        assert "Input JSON is empty." in str(status.render())
