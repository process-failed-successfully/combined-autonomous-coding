import unittest
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from textual.app import App
from typing import Any

from shared.json2xml_lab import Json2XmlManager
from shared.tui_json2xml import Json2XmlTab
from shared.json2xml_lab import run_json2xml_lab_logic
from unittest.mock import patch
import sys
import io


class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestJson2XmlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Json2XmlManager()

    def test_convert_string_simple(self):
        json_str = '{"root": {"item": "Hello"}}'
        expected = "<root>\n  <item>Hello</item>\n</root>"
        result = self.manager.convert_string(json_str)
        self.assertEqual(result, expected)

    def test_convert_string_attributes(self):
        json_str = '{"root": {"@attributes": {"id": "1"}, "item": "World"}}'
        expected = '<root id="1">\n  <item>World</item>\n</root>'
        result = self.manager.convert_string(json_str)
        self.assertEqual(result, expected)

    def test_convert_string_lists(self):
        json_str = '{"root": {"item": ["One", "Two"]}}'
        expected = "<root>\n  <item>One</item>\n  <item>Two</item>\n</root>"
        result = self.manager.convert_string(json_str)
        self.assertEqual(result, expected)

    def test_convert_string_invalid(self):
        json_str = '{"root": {"item": "Hello"}'
        with self.assertRaises(ValueError):
            self.manager.convert_string(json_str)

    def test_convert_file(self):
        json_str = '{"root": {"item": "FileTest"}}'
        expected = "<root>\n  <item>FileTest</item>\n</root>"

        with NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name

        try:
            result = self.manager.convert_file(Path(tmp_path))
            self.assertEqual(result, expected)
        finally:
            os.remove(tmp_path)


class DummyApp(App[Any]):
    def compose(self):
        yield Json2XmlTab()


class TestJson2XmlTui(unittest.IsolatedAsyncioTestCase):
    async def test_tui_render(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set the text attribute directly since it's a TextArea
            app.query_one("#json2xml-input").text = '{"root": {"item": "Test"}}'
            await pilot.click("#btn-convert-json2xml")

            # Check the output
            import asyncio
            await asyncio.sleep(0.1)

            from textual.widgets import TextArea
            output_area = app.query_one("#json2xml-output", TextArea)

            self.assertIn('<item>Test</item>', output_area.text)


class TestJson2XmlCLI(unittest.TestCase):
    def setUp(self):
        self.manager = Json2XmlManager()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_json2xml_lab_logic_text(self, mock_stdout):
        args = DummyArgs(text='{"root": "test"}')
        with self.assertRaises(SystemExit) as cm:
            run_json2xml_lab_logic(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertIn('<root>test</root>', mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_json2xml_lab_logic_file(self, mock_stdout):
        json_str = '{"root": "testfile"}'
        with NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name

        args = DummyArgs(file=tmp_path)
        try:
            with self.assertRaises(SystemExit) as cm:
                run_json2xml_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)
            self.assertIn('<root>testfile</root>', mock_stdout.getvalue())
        finally:
            os.remove(tmp_path)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_json2xml_lab_logic_file_output(self, mock_stdout):
        json_str = '{"root": "testfile"}'
        with NamedTemporaryFile(mode='w', delete=False, suffix=".json") as tmp:
            tmp.write(json_str)
            tmp_path = tmp.name

        out_path = tmp_path + ".xml"

        args = DummyArgs(file=tmp_path, output=out_path)
        try:
            with self.assertRaises(SystemExit) as cm:
                run_json2xml_lab_logic(args)
            self.assertEqual(cm.exception.code, 0)
            self.assertTrue(Path(out_path).exists())
            self.assertIn('<root>testfile</root>', Path(out_path).read_text())
        finally:
            os.remove(tmp_path)
            if os.path.exists(out_path):
                os.remove(out_path)


if __name__ == '__main__':
    unittest.main()
