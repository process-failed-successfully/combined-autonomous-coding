import unittest
import json
import tempfile
import os
import io
import contextlib
import argparse
from unittest.mock import patch, MagicMock

from shared.json2md_lab import Json2MdManager, run_json2md_lab_logic

class TestJson2MdLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2MdManager()

    def test_convert_single_dict(self):
        data = {"name": "Alice", "age": 30, "city": "Wonderland"}
        expected = "| Key | Value |\n| --- | --- |\n| name | Alice |\n| age | 30 |\n| city | Wonderland |"
        res = self.manager.convert(data)
        self.assertEqual(res, expected)

    def test_convert_list_of_dicts(self):
        data = [{"id": 1, "name": "Bob"}, {"id": 2, "name": "Charlie", "role": "admin"}]
        expected = "| id | name | role |\n| --- | --- | --- |\n| 1 | Bob |  |\n| 2 | Charlie | admin |"
        res = self.manager.convert(data)
        self.assertEqual(res, expected)

    def test_convert_list_of_primitives(self):
        data = ["apple", "banana", "cherry"]
        expected = "| Index | Value |\n| --- | --- |\n| 0 | apple |\n| 1 | banana |\n| 2 | cherry |"
        res = self.manager.convert(data)
        self.assertEqual(res, expected)

    def test_convert_nested_objects(self):
        data = {"user": {"id": 1, "name": "Alice"}, "active": True}
        expected = "| Key | Value |\n| --- | --- |\n| user | {\"id\":1,\"name\":\"Alice\"} |\n| active | True |"
        res = self.manager.convert(data)
        self.assertEqual(res, expected)

    def test_run_logic_with_text(self):
        args = argparse.Namespace(text='{"key": "value"}', file=None, output=None, tui=False)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            success = run_json2md_lab_logic(args)

        self.assertTrue(success)
        self.assertIn("| key | value |", output.getvalue())

    def test_run_logic_with_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump([{"a": 1}, {"a": 2}], f)
            temp_name = f.name

        args = argparse.Namespace(file=temp_name, text=None, output=None, tui=False)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            success = run_json2md_lab_logic(args)

        self.assertTrue(success)
        self.assertIn("| a |", output.getvalue())
        os.remove(temp_name)


class DummyApp:
    def notify(self, message, severity="information", timeout=3):
        pass

class TestTuiJson2Md(unittest.IsolatedAsyncioTestCase):
    async def test_tui_components(self):
        from textual.app import App
        from shared.tui_json2md import Json2MdTab

        class MockApp(App):
            def compose(self):
                yield Json2MdTab()

        app = MockApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Json2MdTab)
            # Test empty convert
            await pilot.click("#btn-json2md-convert")

            # Input valid JSON
            input_area = app.query_one("#json2md-input")
            input_area.text = '{"hello": "world"}'
            await pilot.click("#btn-json2md-convert")

            output_area = app.query_one("#json2md-output")
            self.assertIn("| hello | world |", output_area.text)

            # Test clear
            await pilot.click("#btn-json2md-clear")
            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")
