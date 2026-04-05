import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add shared to path
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, RichLog
from textual.app import App, ComposeResult

from shared.tui_pdf import PdfLabTab

class PdfLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield PdfLabTab(project_dir=Path("."))

class TestPdfLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_info_button(self):
        with patch('shared.tui_pdf.PDFLabManager') as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.get_info.return_value = {"/Title": "Test PDF"}

            app = PdfLabTestApp()
            async with app.run_test() as pilot:
                # Set input
                app.query_one("#pdf-input", Input).value = "test.pdf"

                # Mock exists to return True for test.pdf
                with patch('pathlib.Path.exists', return_value=True):
                    pilot.app.query_one("#btn-pdf-info").press()
                    await pilot.pause()

                    # Check log
                    log = app.query_one("#pdf-log", RichLog)
                    # log.lines yields Strip objects. str(strip) might return repr. use .text
                    lines = [line.text for line in log.lines]
                    content = "\n".join(lines)
                    self.assertIn("Metadata for test.pdf", content)
                    self.assertIn("Title: Test PDF", content)

    async def test_text_extract(self):
        with patch('shared.tui_pdf.PDFLabManager') as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.extract_text.return_value = "Extracted text content."

            app = PdfLabTestApp()
            async with app.run_test() as pilot:
                app.query_one("#pdf-input", Input).value = "test.pdf"

                with patch('pathlib.Path.exists', return_value=True):
                    pilot.app.query_one("#btn-pdf-text").press()
                    await pilot.pause()

                    log = app.query_one("#pdf-log", RichLog)
                    lines = [line.text for line in log.lines]
                    content = "\n".join(lines)
                    self.assertIn("Extracting text from test.pdf", content)
                    self.assertIn("Extracted text content.", content)

    async def test_file_not_found(self):
        # Patch PDFLabManager so it doesn't error out on init if pypdf is missing
        with patch('shared.tui_pdf.PDFLabManager'):
            app = PdfLabTestApp()
            async with app.run_test() as pilot:
                app.query_one("#pdf-input", Input).value = "nonexistent.pdf"

                with patch('pathlib.Path.exists', return_value=False):
                    pilot.app.query_one("#btn-pdf-info").press()
                    await pilot.pause()

                    log = app.query_one("#pdf-log", RichLog)
                    lines = [line.text for line in log.lines]
                    content = "\n".join(lines)
                    # Should be empty because it returns early
                    self.assertEqual(content, "")

    async def test_split_button(self):
        with patch('shared.tui_pdf.PDFLabManager') as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.split_pdf.return_value = ["page_1.pdf", "page_2.pdf"]

            app = PdfLabTestApp()
            async with app.run_test() as pilot:
                app.query_one("#pdf-input", Input).value = "test.pdf"

                with patch('pathlib.Path.exists', return_value=True):
                    pilot.app.query_one("#btn-pdf-split").press()
                    await pilot.pause()

                    log = app.query_one("#pdf-log", RichLog)
                    lines = [line.text for line in log.lines]
                    content = "\n".join(lines)
                    self.assertIn("Splitting test.pdf...", content)
                    self.assertIn("Split into 2 pages", content)
