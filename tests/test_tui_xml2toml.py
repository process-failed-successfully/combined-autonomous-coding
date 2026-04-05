import pytest
from textual.app import App
from shared.tui_xml2toml import Xml2TomlTab
from textual.widgets import Select


class DummyApp(App[None]):
    def compose(self):
        yield Xml2TomlTab()


@pytest.mark.asyncio
async def test_xml2toml_tab_initialization():
    app = DummyApp()
    async with app.run_test(size=(200, 200)):
        assert app.query_one(Xml2TomlTab) is not None


@pytest.mark.asyncio
async def test_xml2toml_tab_conversion_success():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        tab = app.query_one(Xml2TomlTab)
        input_area = tab.query_one("#input_area")
        output_area = tab.query_one("#output_area")

        # Test XML to TOML
        input_area.text = "<data><name>Test</name></data>"
        app.query_one("#convert_btn").press()
        await pilot.pause()
        assert "Test" in output_area.text

        # Test TOML to XML
        tab.mode = "toml2xml"
        input_area.text = 'name = "Test2"'
        app.query_one("#convert_btn").press()
        await pilot.pause()
        assert "Test2" in output_area.text


@pytest.mark.asyncio
async def test_xml2toml_tab_conversion_empty():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        tab = app.query_one(Xml2TomlTab)
        input_area = tab.query_one("#input_area")

        # Test empty
        input_area.text = ""
        app.query_one("#convert_btn").press()
        await pilot.pause()
        status = tab.query_one("#status_bar").renderable
        assert str(status) == "Error: Input is empty."


@pytest.mark.asyncio
async def test_xml2toml_tab_conversion_error():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        tab = app.query_one(Xml2TomlTab)
        input_area = tab.query_one("#input_area")

        # Test invalid XML
        input_area.text = "<data><name>Test</data>"
        app.query_one("#convert_btn").press()
        await pilot.pause()
        status = tab.query_one("#status_bar").renderable
        assert "Error:" in str(status)


@pytest.mark.asyncio
async def test_xml2toml_tab_clear():
    app = DummyApp()
    async with app.run_test(size=(200, 200)) as pilot:
        tab = app.query_one(Xml2TomlTab)
        input_area = tab.query_one("#input_area")
        output_area = tab.query_one("#output_area")

        input_area.text = "test"
        output_area.text = "test"
        app.query_one("#clear_btn").press()
        await pilot.pause()
        assert input_area.text == ""
        assert output_area.text == ""


@pytest.mark.asyncio
async def test_xml2toml_tab_mode_select():
    app = DummyApp()
    async with app.run_test(size=(200, 200)):
        tab = app.query_one(Xml2TomlTab)
        select = tab.query_one("#mode_select")

        class DummyEvent:
            def __init__(self, select, value):
                self.select = select
                self.value = value

        tab.on_select_changed(DummyEvent(select, "toml2xml"))
        assert tab.mode == "toml2xml"

        tab.on_select_changed(DummyEvent(select, Select.BLANK))
        assert tab.mode == "toml2xml"  # unchanged
