import unittest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO
import argparse

sys.path.append(str(Path(__file__).parent.parent))

from shared.regex_escape_lab import RegexEscapeManager, run_regex_escape_lab_logic


class TestRegexEscapeLab(unittest.TestCase):

    def setUp(self):
        self.manager = RegexEscapeManager()

    def test_escape(self):
        self.assertEqual(self.manager.escape(""), "")
        self.assertEqual(self.manager.escape("hello"), "hello")
        self.assertEqual(self.manager.escape("hello world"), "hello\\ world")
        self.assertEqual(self.manager.escape("*.+?{}[]()|^$\\"), "\\*\\.\\+\\?\\{\\}\\[\\]\\(\\)\\|\\^\\$\\\\")

    def test_unescape(self):
        self.assertEqual(self.manager.unescape(""), "")
        self.assertEqual(self.manager.unescape("hello"), "hello")
        self.assertEqual(self.manager.unescape("hello\\ world"), "hello world")
        self.assertEqual(self.manager.unescape("\\*\\.\\+\\?\\{\\}\\[\\]\\(\\)\\|\\^\\$\\\\"), "*.+?{}[]()|^$\\")

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_regex_escape_lab_logic_encode(self, mock_stdout):
        args = argparse.Namespace(encode="a.b")
        success = run_regex_escape_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "a\\.b")

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_regex_escape_lab_logic_decode(self, mock_stdout):
        args = argparse.Namespace(decode="a\\.b")
        success = run_regex_escape_lab_logic(args)
        self.assertTrue(success)
        self.assertEqual(mock_stdout.getvalue().strip(), "a.b")

    @patch('sys.stderr', new_callable=StringIO)
    def test_run_regex_escape_lab_logic_no_args(self, mock_stderr):
        args = argparse.Namespace()
        success = run_regex_escape_lab_logic(args)
        self.assertFalse(success)
        self.assertIn("Error: No action specified", mock_stderr.getvalue())

    def test_main_parser(self):
        import main

        # Test encode parsing
        args = main.parse_args(["regex-escape-lab", "--encode", "hello.world"])
        self.assertEqual(args.command, "regex-escape-lab")
        self.assertEqual(args.encode, "hello.world")
        self.assertFalse(args.tui)

        # Test decode parsing
        args = main.parse_args(["regex-escape-lab", "--decode", "hello\\.world"])
        self.assertEqual(args.command, "regex-escape-lab")
        self.assertEqual(args.decode, "hello\\.world")
        self.assertFalse(args.tui)

        # Test tui parsing
        args = main.parse_args(["regex-escape-lab", "--tui"])
        self.assertEqual(args.command, "regex-escape-lab")
        self.assertTrue(args.tui)


class TestRegexEscapeLabTUI(unittest.IsolatedAsyncioTestCase):

    async def test_tui_render(self):
        try:
            from textual.app import App, ComposeResult
            from shared.tui_regex_escape import RegexEscapeLabTab

            class DummyApp(App):
                def compose(self) -> ComposeResult:
                    yield RegexEscapeLabTab()

            app = DummyApp()
            async with app.run_test() as pilot:
                tab = app.query_one(RegexEscapeLabTab)
                self.assertIsNotNone(tab)

                # Test logic within UI
                input_area = app.query_one("#regex-escape-input")
                output_area = app.query_one("#regex-escape-output")

                # Test escape
                input_area.text = "a.b"
                await pilot.click("#btn-regex-escape")
                self.assertEqual(output_area.text, "a\\.b")

                # Test unescape
                input_area.text = "a\\.b"
                await pilot.click("#btn-regex-unescape")
                self.assertEqual(output_area.text, "a.b")

                # Test clear
                await pilot.click("#btn-regex-clear")
                self.assertEqual(input_area.text, "")
                self.assertEqual(output_area.text, "")

        except ImportError:
            self.skipTest("Textual not installed")
