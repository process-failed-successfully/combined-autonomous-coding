import unittest
from textual.app import App
from typing import Any
from textual.widgets import TextArea, Select, Static

from shared.tui_xml2yaml import Xml2YamlTab


class DummyApp(App[Any]):
    def compose(self):
        yield Xml2YamlTab()


class TestXml2YamlTUI(unittest.IsolatedAsyncioTestCase):
    async def test_initialization(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(Xml2YamlTab)
            assert tab.mode == "xml2yaml"
            input_area = app.query_one("#input_area", TextArea)

            status = app.query_one("#status_bar", Static)
            assert "xml2yaml" in str(status.render())

    async def test_conversion_xml_to_yaml(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#input_area", TextArea)
            input_area.text = "<root><child>value</child></root>"

            # click convert button
            pilot.app.query_one("#convert_btn").press()
            await pilot.pause()

            output_area = app.query_one("#output_area", TextArea)
            assert "root:" in output_area.text
            assert "child: value" in output_area.text

            status = app.query_one("#status_bar", Static)
            assert "Successfully" in str(status.render())

    async def test_mode_switch_and_conversion(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Change mode to yaml2xml
            select = app.query_one("#mode_select", Select)
            select.value = "yaml2xml"
            await pilot.pause()

            tab = app.query_one(Xml2YamlTab)
            assert tab.mode == "yaml2xml"

            input_area = app.query_one("#input_area", TextArea)

            input_area.text = "root:\n  child: value\n"

            # Click convert
            pilot.app.query_one("#convert_btn").press()
            await pilot.pause()

            output_area = app.query_one("#output_area", TextArea)
            assert "<root>" in output_area.text
            assert "<child>value</child>" in output_area.text

    async def test_conversion_error(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#input_area", TextArea)
            input_area.text = "<root><unclosed>error</root>"

            pilot.app.query_one("#convert_btn").press()
            await pilot.pause()

            status = app.query_one("#status_bar", Static)
            assert "Error" in str(status.render())

    async def test_clear_button(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_area = app.query_one("#input_area", TextArea)
            input_area.text = "<test/>"

            pilot.app.query_one("#clear_btn").press()
            await pilot.pause()

            assert input_area.text == ""
            output_area = app.query_one("#output_area", TextArea)
            assert output_area.text == ""
            status = app.query_one("#status_bar", Static)
            assert "Cleared all fields" in str(status.render())
