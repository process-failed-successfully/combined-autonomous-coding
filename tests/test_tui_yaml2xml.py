import pytest
from textual.app import App


try:
    from shared.tui_yaml2xml import Yaml2XmlTab
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

if HAS_TEXTUAL:
    class DummyApp(App):
        def compose(self):
            yield Yaml2XmlTab()

@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_TEXTUAL, reason="Textual not installed")
async def test_yaml2xml_tab_conversion():
    app = DummyApp()
    async with app.run_test() as pilot:
        # Get the tab


        # Find text areas
        input_area = app.query_one("#yaml2xml-input")
        output_area = app.query_one("#yaml2xml-output")

        # Test 1: Empty input
        input_area.text = ""
        await pilot.click("#btn-yaml2xml-convert")
        await pilot.pause()
        assert output_area.text == ""

        # Test 2: Valid YAML
        input_area.text = "user:\n  name: Test\n  age: 99"
        await pilot.click("#btn-yaml2xml-convert")
        await pilot.pause()
        assert "<user>" in output_area.text
        assert "<name>Test</name>" in output_area.text
        assert "<age>99</age>" in output_area.text

        # Test 3: Invalid YAML
        input_area.text = "invalid:\n  - : yaml\n::::"
        await pilot.click("#btn-yaml2xml-convert")
        await pilot.pause()
        assert "Error" in output_area.text

        # Test 4: Clear button
        await pilot.click("#btn-yaml2xml-clear")
        await pilot.pause()
        assert input_area.text == ""
        assert output_area.text == ""
