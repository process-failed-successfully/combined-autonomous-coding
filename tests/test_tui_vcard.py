import unittest
import sys
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_vcard import VCardTab
from textual.widgets import Input, TextArea, RichLog
from textual.app import App

class DummyApp(App[None]):
    def __init__(self, tab_widget):
        super().__init__()
        self.tab_widget = tab_widget

    def compose(self):
        yield self.tab_widget

class TestVCardTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.tab = VCardTab(self.test_dir)
        self.app = DummyApp(self.tab)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_generate_vcard(self):
        async with self.app.run_test() as pilot:
            # Fill in some inputs
            self.tab.query_one("#vcard-fn", Input).value = "Test User"
            self.tab.query_one("#vcard-email", Input).value = "test@example.com"
            self.tab.query_one("#vcard-note", Input).value = "Test Note"

            # Directly call handler to bypass pilot out of bounds error
            self.tab.on_generate()
            await pilot.pause()

            log = self.tab.query_one("#vcard-gen-output", RichLog)
            output = "\n".join([str(line.text.plain if hasattr(line.text, 'plain') else line.text) for line in log.lines])

            self.assertIn("BEGIN:VCARD", output)
            self.assertIn("FN:Test User", output)
            self.assertIn("EMAIL;TYPE=INTERNET:test@example.com", output)
            self.assertIn("NOTE:Test Note", output)

    async def test_parse_vcard(self):
        async with self.app.run_test() as pilot:
            # Fill in text area
            vcard_text = """BEGIN:VCARD
VERSION:3.0
FN:Parsed User
EMAIL;TYPE=INTERNET:parsed@example.com
END:VCARD"""
            self.tab.query_one("#vcard-parse-input", TextArea).text = vcard_text

            # Directly call handler to bypass pilot out of bounds error
            self.tab.on_parse()
            await pilot.pause()

            log = self.tab.query_one("#vcard-parse-output", RichLog)
            output = "\n".join([str(line.text.plain if hasattr(line.text, 'plain') else line.text) for line in log.lines])

            self.assertIn("Parsed User", output)
            self.assertIn("parsed@example.com", output)
