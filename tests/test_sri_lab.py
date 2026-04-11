import unittest
import base64
import hashlib
from unittest.mock import patch, MagicMock
import tempfile
import os

from shared.sri_lab import SriManager

class TestSriManager(unittest.TestCase):
    def setUp(self):
        self.manager = SriManager()

    def test_compute_hashes(self):
        content = b"console.log('Hello');"

        # Manually compute expected hashes
        expected_sha256 = base64.b64encode(hashlib.sha256(content).digest()).decode('utf-8')
        expected_sha384 = base64.b64encode(hashlib.sha384(content).digest()).decode('utf-8')
        expected_sha512 = base64.b64encode(hashlib.sha512(content).digest()).decode('utf-8')

        hashes = self.manager.compute_hashes(content)

        self.assertEqual(hashes['sha256'], f"sha256-{expected_sha256}")
        self.assertEqual(hashes['sha384'], f"sha384-{expected_sha384}")
        self.assertEqual(hashes['sha512'], f"sha512-{expected_sha512}")

    def test_generate_html_tag_js(self):
        tag = self.manager.generate_html_tag("script.js", "sha384-abc")
        self.assertEqual(tag, '<script src="script.js" integrity="sha384-abc" crossorigin="anonymous"></script>')

    def test_generate_html_tag_css(self):
        tag = self.manager.generate_html_tag("styles.css", "sha384-abc")
        self.assertEqual(tag, '<link rel="stylesheet" href="styles.css" integrity="sha384-abc" crossorigin="anonymous">')

    @patch('urllib.request.urlopen')
    def test_fetch_content_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"url_content"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        content = self.manager.fetch_content("https://example.com/test.js")
        self.assertEqual(content, b"url_content")
        mock_urlopen.assert_called_once()

    def test_fetch_content_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"file_content")
            temp_path = f.name

        try:
            content = self.manager.fetch_content(temp_path)
            self.assertEqual(content, b"file_content")
        finally:
            os.remove(temp_path)

    def test_fetch_content_file_not_found(self):
        with self.assertRaisesRegex(ValueError, "File not found"):
            self.manager.fetch_content("does_not_exist.js")


from textual.app import App
from typing import Any
from shared.tui_sri import SriLabTab
from textual.widgets import Input, TextArea, Button, Select

class DummyApp(App[Any]):
    def compose(self):
        yield SriLabTab()

class TestSriLabTab(unittest.IsolatedAsyncioTestCase):
    @patch('shared.sri_lab.SriManager.fetch_content')
    async def test_generate_sri_ui(self, mock_fetch):
        mock_fetch.return_value = b"console.log('UI');"

        app = DummyApp()
        async with app.run_test() as pilot:
            # Set input
            source_input = app.query_one("#sri_source_input", Input)
            source_input.value = "https://example.com/script.js"

            # Select algo
            algo_select = app.query_one("#sri_algo_select", Select)
            algo_select.value = "sha256"

            # Click generate
            await pilot.click("#btn_sri_generate")
            await pilot.pause()

            # Verify fetch was called
            mock_fetch.assert_called_once_with("https://example.com/script.js")

            # Check outputs
            hash_out = app.query_one("#sri_hash_output", Input)
            tag_out = app.query_one("#sri_tag_output", TextArea)

            self.assertTrue(hash_out.value.startswith("sha256-"))
            self.assertIn("integrity=\"sha256-", tag_out.text)
            self.assertIn("script.js", tag_out.text)

    async def test_clear_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Set values
            app.query_one("#sri_source_input", Input).value = "test"
            app.query_one("#sri_hash_output", Input).value = "hash"
            app.query_one("#sri_tag_output", TextArea).text = "tag"

            # Click clear
            await pilot.click("#btn_sri_clear")
            await pilot.pause()

            # Check cleared
            self.assertEqual(app.query_one("#sri_source_input", Input).value, "")
            self.assertEqual(app.query_one("#sri_hash_output", Input).value, "")
            self.assertEqual(app.query_one("#sri_tag_output", TextArea).text, "")
