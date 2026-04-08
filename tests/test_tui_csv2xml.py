import pytest
import pytest_asyncio
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Input, Button
from shared.tui_csv2xml import Csv2XmlLabTab

class Csv2XmlTestApp(App):
    """Test app for Csv2XmlLabTab."""
    def compose(self) -> ComposeResult:
        yield Csv2XmlLabTab()

@pytest.mark.asyncio
async def test_csv2xml_lab_tab_conversion():
    app = Csv2XmlTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Csv2XmlLabTab)

        # Test basic conversion
        input_ta = app.query_one("#c2x-input", TextArea)
        output_ta = app.query_one("#c2x-output", TextArea)

        # Verify initial state
        assert input_ta.text == ""
        assert output_ta.text == ""

        # Provide input
        input_ta.text = "name,age\nAlice,30\nBob,25"

        # Trigger conversion
        tab.action_convert()
        await pilot.pause()

        # Verify output
        assert "<root>" in output_ta.text
        assert "<item>" in output_ta.text
        assert "<name>Alice</name>" in output_ta.text
        assert "<age>30</age>" in output_ta.text

@pytest.mark.asyncio
async def test_csv2xml_lab_tab_custom_tags():
    app = Csv2XmlTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Csv2XmlLabTab)

        # Set inputs
        app.query_one("#c2x-input", TextArea).text = "name,age\nAlice,30"
        app.query_one("#c2x-root", Input).value = "users"
        app.query_one("#c2x-item", Input).value = "user"

        # Convert
        tab.action_convert()
        await pilot.pause()

        # Verify output
        output = app.query_one("#c2x-output", TextArea).text
        assert "<users>" in output
        assert "</users>" in output
        assert "<user>" in output
        assert "</user>" in output
        assert "<name>Alice</name>" in output

@pytest.mark.asyncio
async def test_csv2xml_lab_tab_clear_all():
    app = Csv2XmlTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(Csv2XmlLabTab)

        # Set all inputs
        app.query_one("#c2x-input", TextArea).text = "a,b\n1,2"
        app.query_one("#c2x-output", TextArea).text = "some output"
        app.query_one("#c2x-delimiter", Input).value = ";"
        app.query_one("#c2x-root", Input).value = "dataset"
        app.query_one("#c2x-item", Input).value = "record"

        # Trigger clear_all action
        await pilot.press("ctrl+c")

        # Verify everything is cleared
        assert app.query_one("#c2x-input", TextArea).text == ""
        assert app.query_one("#c2x-output", TextArea).text == ""
        assert app.query_one("#c2x-delimiter", Input).value == ""
        assert app.query_one("#c2x-root", Input).value == ""
        assert app.query_one("#c2x-item", Input).value == ""
