import pytest
from textual.app import App
from typing import Any
import unittest
from unittest.mock import patch
import io
import argparse
import sys

from shared.json2dart_lab import Json2DartManager, run_json2dart_lab_logic
from shared.tui_json2dart import Json2DartLabTab
from textual.widgets import TextArea, Input, Static


class TestJson2DartManager:
    @pytest.fixture
    def manager(self):
        return Json2DartManager()

    def test_basic_conversion(self, manager):
        json_data = '{"name": "Alice", "age": 30, "isActive": true}'
        dart_code = manager.convert(json_data, "User")

        assert "class User {" in dart_code
        assert "String? name;" in dart_code
        assert "int? age;" in dart_code
        assert "bool? isActive;" in dart_code
        assert "User({" in dart_code
        assert "this.name," in dart_code
        assert "factory User.fromJson(Map<String, dynamic> json)" in dart_code
        assert "Map<String, dynamic> toJson()" in dart_code

    def test_nested_objects(self, manager):
        json_data = '{"user": {"name": "Bob"}}'
        dart_code = manager.convert(json_data, "Response")

        assert "class User {" in dart_code
        assert "class Response {" in dart_code
        assert "User? user;" in dart_code
        assert "User.fromJson(json['user'])" in dart_code

    def test_lists(self, manager):
        json_data = '{"items": [{"id": 1}], "tags": ["a", "b"]}'
        dart_code = manager.convert(json_data, "Data")

        assert "class Item {" in dart_code
        assert "List<Item>? items;" in dart_code
        assert "List<String>? tags;" in dart_code
        assert "(json['items'] as List).map((i) => Item.fromJson(i)).toList()" in dart_code
        assert "List<String>.from(json['tags'])" in dart_code

    def test_invalid_json(self, manager):
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.convert('{"bad": json')

def test_run_json2dart_lab_logic_cli_stdout():
    args = argparse.Namespace(action=None, text='{"key": "value"}', file=None, name="MyClass", output=None, tui=False)
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        success = run_json2dart_lab_logic(args)

    assert success is True
    output = mock_stdout.getvalue()
    assert "class MyClass" in output
    assert "String? key;" in output


class DummyApp(App[Any]):
    def compose(self):
        yield Json2DartLabTab()


class TestJson2DartLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#json2dart-input-ta", TextArea)
            input_ta.text = '{"name": "test"}'

            name_input = app.query_one("#json2dart-name-input", Input)
            name_input.value = "TestClass"

            btn = app.query_one("#json2dart-convert-btn")
            event = unittest.mock.MagicMock()
            event.button.id = btn.id
            await app.query_one('Json2DartLabTab').on_button_pressed(event)

            output_ta = app.query_one("#json2dart-output-ta", TextArea)
            assert "class TestClass" in output_ta.text
            assert "String? name;" in output_ta.text

            status = app.query_one("#json2dart-status", Static)
            assert "Conversion successful" in str(status.render())

    async def test_empty_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            btn = app.query_one("#json2dart-convert-btn")
            event = unittest.mock.MagicMock()
            event.button.id = btn.id
            await app.query_one('Json2DartLabTab').on_button_pressed(event)

            status = app.query_one("#json2dart-status", Static)
            assert "Input is empty" in str(status.render())

    async def test_invalid_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#json2dart-input-ta", TextArea)
            input_ta.text = '{"invalid":'

            btn = app.query_one("#json2dart-convert-btn")
            event = unittest.mock.MagicMock()
            event.button.id = btn.id
            await app.query_one('Json2DartLabTab').on_button_pressed(event)

            status = app.query_one("#json2dart-status", Static)
            assert "Error" in str(status.render())
