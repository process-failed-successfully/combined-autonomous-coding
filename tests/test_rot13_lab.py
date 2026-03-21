import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_rot13 import Rot13LabTab
from shared.rot13_lab import run_rot13_lab_logic
from textual.widgets import TextArea

class DummyApp(App[None]):
    def __init__(self):
        super().__init__()
        self.tab = Rot13LabTab()

    def compose(self) -> ComposeResult:
        yield self.tab

class TestRot13Lab(unittest.IsolatedAsyncioTestCase):
    def test_run_logic_with_text(self):
        args = MagicMock()
        args.text = "Hello"
        args.tui = False

        with patch("sys.stdout") as mock_stdout:
            result = run_rot13_lab_logic(args)
            self.assertTrue(result)
            mock_stdout.write.assert_any_call("Uryyb")

    def test_run_logic_stdin(self):
        args = MagicMock()
        args.text = None
        args.tui = False

        with patch("sys.stdin.isatty", return_value=False), \
             patch("sys.stdin.read", return_value="Hello"), \
             patch("sys.stdout") as mock_stdout:
            result = run_rot13_lab_logic(args)
            self.assertTrue(result)
            mock_stdout.write.assert_any_call("Uryyb")

    def test_run_logic_missing_input(self):
        args = MagicMock()
        args.text = None
        args.tui = False

        with patch("sys.stdin.isatty", return_value=True):
            result = run_rot13_lab_logic(args)
            self.assertFalse(result)

    async def test_tui_rot13_tab(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Type into input area
            input_area = app.query_one("#rot13-input", TextArea)
            input_area.text = "Hello World"

            # Wait for event to process
            await pilot.pause()

            output_area = app.query_one("#rot13-output", TextArea)
            self.assertEqual(output_area.text, "Uryyb Jbeyq")

            # Clear input
            input_area.text = ""
            await pilot.pause()
            self.assertEqual(output_area.text, "")
