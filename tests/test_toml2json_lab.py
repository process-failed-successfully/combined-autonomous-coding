import pytest
from textual.app import App
from typing import Any
import unittest
from shared.toml2json_lab import Toml2JsonManager
from shared.tui_toml2json import Toml2JsonLabTab
from textual.widgets import TextArea, Select, Static


class TestToml2JsonManager:

    @pytest.fixture
    def manager(self):
        return Toml2JsonManager()

    def test_convert_toml_to_json_valid(self, manager):
        toml_input = 'title = "TOML Example"\n\n[owner]\nname = "Tom Preston-Werner"'
        json_output = manager.convert_toml_to_json(toml_input)
        assert '"title": "TOML Example"' in json_output
        assert '"owner": {' in json_output
        assert '"name": "Tom Preston-Werner"' in json_output

    def test_convert_toml_to_json_invalid(self, manager):
        with pytest.raises(ValueError, match="Invalid TOML"):
            manager.convert_toml_to_json('invalid_toml = [1, 2,')

    def test_convert_json_to_toml_valid(self, manager):
        json_input = '{"title": "JSON Example", "owner": {"name": "Tom"}}'
        toml_output = manager.convert_json_to_toml(json_input)
        assert 'title = "JSON Example"' in toml_output
        assert '[owner]' in toml_output
        assert 'name = "Tom"' in toml_output

    def test_convert_json_to_toml_invalid(self, manager):
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.convert_json_to_toml('{"invalid": json}')

    def test_convert_json_to_toml_not_dict(self, manager):
        with pytest.raises(ValueError, match="must be an object"):
            manager.convert_json_to_toml('[1, 2, 3]')


class DummyApp(App[Any]):
    def compose(self):
        yield Toml2JsonLabTab()


class TestToml2JsonLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_toml_to_json_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set input
            input_ta = app.query_one("#toml2json-input-ta", TextArea)
            input_ta.text = 'key = "value"'

            # Ensure mode is TOML to JSON
            mode_select = app.query_one("#toml2json-mode-select", Select)
            mode_select.value = "toml2json"

            # Click convert
            await pilot.click("#toml2json-convert-btn")

            # Check output
            output_ta = app.query_one("#toml2json-output-ta", TextArea)
            assert '"key": "value"' in output_ta.text

            status = app.query_one("#toml2json-status", Static)
            assert "Conversion successful" in str(status.render())

    async def test_convert_json_to_toml_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set input
            input_ta = app.query_one("#toml2json-input-ta", TextArea)
            input_ta.text = '{"key": "value"}'

            # Set mode to JSON to TOML
            mode_select = app.query_one("#toml2json-mode-select", Select)
            mode_select.value = "json2toml"

            # Click convert
            await pilot.click("#toml2json-convert-btn")

            # Check output
            output_ta = app.query_one("#toml2json-output-ta", TextArea)
            assert 'key = "value"' in output_ta.text

            status = app.query_one("#toml2json-status", Static)
            assert "Conversion successful" in str(status.render())

    async def test_empty_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Click convert without input
            await pilot.click("#toml2json-convert-btn")

            status = app.query_one("#toml2json-status", Static)
            assert "Input is empty" in str(status.render())

    async def test_invalid_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set invalid JSON input
            input_ta = app.query_one("#toml2json-input-ta", TextArea)
            input_ta.text = '{"key":'

            # Set mode to JSON to TOML
            mode_select = app.query_one("#toml2json-mode-select", Select)
            mode_select.value = "json2toml"

            # Click convert
            await pilot.click("#toml2json-convert-btn")

            status = app.query_one("#toml2json-status", Static)
            assert "Error" in str(status.render())
