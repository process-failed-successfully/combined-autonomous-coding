import pytest
from textual.app import App
from typing import Any
import unittest
from shared.env2json_lab import Env2JsonManager
from shared.tui_env2json import Env2JsonTab
from textual.widgets import TextArea, Select


class TestEnv2JsonManager:

    @pytest.fixture
    def manager(self):
        return Env2JsonManager()

    def test_env_to_json_valid(self, manager):
        env_input = 'API_KEY="secret123"\nDEBUG=true\n# This is a comment\nPORT=8080'
        json_output = manager.env_to_json(env_input)
        assert json_output == {"API_KEY": "secret123", "DEBUG": "true", "PORT": "8080"}

    def test_json_to_env_valid(self, manager):
        json_input = '{"API_KEY": "secret123", "DEBUG": true, "PORT": 8080}'
        env_output = manager.json_to_env(json_input)
        assert 'API_KEY=secret123' in env_output
        assert 'DEBUG=True' in env_output
        assert 'PORT=8080' in env_output

    def test_json_to_env_invalid(self, manager):
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.json_to_env('{"invalid": json}')

    def test_json_to_env_not_dict(self, manager):
        with pytest.raises(ValueError, match="must be an object"):
            manager.json_to_env('["invalid"]')

    def test_json_to_env_with_spaces(self, manager):
        json_input = '{"MESSAGE": "Hello World"}'
        env_output = manager.json_to_env(json_input)
        assert 'MESSAGE="Hello World"' in env_output


class DummyApp(App[Any]):
    def compose(self):
        yield Env2JsonTab()


class TestEnv2JsonLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_env_to_json_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#env2json_input", TextArea)
            input_ta.text = 'KEY=value'

            mode_select = app.query_one("#env2json_mode_select", Select)
            mode_select.value = "env2json"

            await pilot.click("#btn_convert")

            output_ta = app.query_one("#env2json_output", TextArea)
            assert '"KEY": "value"' in output_ta.text

    async def test_convert_json_to_env_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#env2json_input", TextArea)
            input_ta.text = '{"KEY": "value"}'

            mode_select = app.query_one("#env2json_mode_select", Select)
            mode_select.value = "json2env"

            await pilot.click("#btn_convert")

            output_ta = app.query_one("#env2json_output", TextArea)
            assert 'KEY=value' in output_ta.text

    async def test_empty_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            await pilot.click("#btn_convert")
            # Usually raises a notification, testing that it doesn't crash
            output_ta = app.query_one("#env2json_output", TextArea)
            assert output_ta.text == ""

    async def test_invalid_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#env2json_input", TextArea)
            input_ta.text = '{"KEY":'

            mode_select = app.query_one("#env2json_mode_select", Select)
            mode_select.value = "json2env"

            await pilot.click("#btn_convert")

            # Expect notification or output to remain empty on failure
            output_ta = app.query_one("#env2json_output", TextArea)
            assert output_ta.text == ""
