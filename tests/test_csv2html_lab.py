import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import argparse
from shared.csv2html_lab import Csv2HtmlManager, run_csv2html_lab_logic


class TestCsv2HtmlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2HtmlManager()

    def test_convert_basic(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        html = self.manager.convert(csv_data)
        self.assertIn("<table>", html)
        self.assertIn("<th>name</th>", html)
        self.assertIn("<th>age</th>", html)
        self.assertIn("<td>Alice</td>", html)
        self.assertIn("<td>30</td>", html)

    def test_convert_no_header(self):
        csv_data = "Alice,30\nBob,25"
        html = self.manager.convert(csv_data, has_header=False)
        self.assertIn("<table>", html)
        self.assertNotIn("<thead>", html)
        self.assertIn("<td>Alice</td>", html)

    def test_convert_with_attrs(self):
        csv_data = "a,b\n1,2"
        html = self.manager.convert(csv_data, table_class="table-cls", table_id="table-id")
        self.assertIn('<table id="table-id" class="table-cls">', html)

    def test_convert_empty(self):
        self.assertEqual(self.manager.convert(""), "")

    def test_escape_html(self):
        csv_data = "name,tag\nAlice,<b>bold</b>"
        html = self.manager.convert(csv_data)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", html)

class TestCsv2HtmlLabCLI(unittest.TestCase):
    @patch('sys.exit')
    @patch('builtins.print')
    def test_cli_text_success(self, mock_print, mock_exit):
        args = argparse.Namespace(
            text="a,b\n1,2",
            file=None,
            delimiter=",",
            no_header=False,
            table_class="",
            table_id="",
            output=None,
            tui=False
        )
        result = run_csv2html_lab_logic(args)
        self.assertTrue(result)
        # Check print was called
        self.assertTrue(any("<table>" in str(c) for c in mock_print.mock_calls))

    @patch('sys.exit')
    @patch('builtins.print')
    def test_cli_file_success(self, mock_print, mock_exit):
        args = argparse.Namespace(
            text=None,
            file="test.csv",
            delimiter=",",
            no_header=False,
            table_class="",
            table_id="",
            output=None,
            tui=False
        )
        with patch('builtins.open', mock_open(read_data="a,b\n1,2")):
            result = run_csv2html_lab_logic(args)
            self.assertTrue(result)
            self.assertTrue(any("<table>" in str(c) for c in mock_print.mock_calls))

    @patch('sys.exit')
    @patch('builtins.print')
    def test_cli_missing_input(self, mock_print, mock_exit):
        args = argparse.Namespace(
            text=None,
            file=None,
            delimiter=",",
            no_header=False,
            table_class="",
            table_id="",
            output=None,
            tui=False
        )
        with patch('sys.stdin.isatty', return_value=True):
            run_csv2html_lab_logic(args)
            mock_exit.assert_called_with(1)


class TestCsv2HtmlLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_tui_instantiation_and_actions(self):
        import pytest
        pytest.importorskip("textual")
        from textual.app import App
        from typing import Any
        from shared.tui_csv2html import Csv2HtmlLabTab
        from textual.widgets import Input, TextArea, RichLog, Checkbox

        class DummyApp(App[Any]):
            def compose(self):
                yield Csv2HtmlLabTab(project_dir=Path("."))

        app = DummyApp()
        async with app.run_test(size=(80, 24)) as pilot:
            tab = app.query_one(Csv2HtmlLabTab)
            self.assertIsNotNone(tab)

            # Test empty convert
            pilot.app.query_one("#btn-convert-csv2html").press()
            await pilot.pause()
            log = app.query_one("#csv2html-log", RichLog)
            self.assertIn("No input CSV provided.", str(list(log.lines)))

            # Test valid convert
            app.query_one("#csv-input", TextArea).load_text("a,b\n1,2")
            pilot.app.query_one("#btn-convert-csv2html").press()
            await pilot.pause()
            output = app.query_one("#html-output", TextArea).text
            self.assertIn("<table>", output)
            self.assertIn("<th>a</th>", output)

            # Test clear
            pilot.app.query_one("#btn-clear-csv2html").press()
            await pilot.pause()
            self.assertEqual(app.query_one("#csv-input", TextArea).text, "")
            self.assertEqual(app.query_one("#html-output", TextArea).text, "")


if __name__ == '__main__':
    pass
