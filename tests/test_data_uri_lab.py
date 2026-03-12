import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os
import sys
import argparse

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_uri_lab import DataUriLabManager, run_data_uri_lab_logic

class TestDataUriLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = DataUriLabManager()

    def test_encode_text_base64(self):
        text = "Hello, World!"
        # "Hello, World!" in base64 is "SGVsbG8sIFdvcmxkIQ=="
        expected = "data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="
        result = self.manager.encode_text(text)
        self.assertEqual(result, expected)

    def test_encode_text_custom_mime(self):
        text = "<h1>Hello</h1>"
        expected = "data:text/html;base64,PGgxPkhlbGxvPC9oMT4="
        result = self.manager.encode_text(text, mime_type="text/html")
        self.assertEqual(result, expected)

    def test_encode_text_url_encoded(self):
        text = "Hello, World!"
        # URL encoded: Hello%2C%20World%21
        expected = "data:text/plain,Hello%2C%20World%21"
        result = self.manager.encode_text(text, use_base64=False)
        self.assertEqual(result, expected)

    def test_encode_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_file.write(b"File content")
            temp_filepath = temp_file.name

        try:
            # "File content" in base64 is "RmlsZSBjb250ZW50"
            expected = "data:text/plain;base64,RmlsZSBjb250ZW50"
            result = self.manager.encode_file(temp_filepath)
            self.assertEqual(result, expected)
        finally:
            os.unlink(temp_filepath)

    def test_decode_base64(self):
        uri = "data:text/html;base64,PGgxPkhlbGxvPC9oMT4="
        result = self.manager.decode(uri)
        self.assertEqual(result["mime_type"], "text/html")
        self.assertTrue(result["is_base64"])
        self.assertEqual(result["data"], b"<h1>Hello</h1>")

    def test_decode_url_encoded(self):
        uri = "data:text/plain,Hello%2C%20World%21"
        result = self.manager.decode(uri)
        self.assertEqual(result["mime_type"], "text/plain")
        self.assertFalse(result["is_base64"])
        self.assertEqual(result["data"], b"Hello, World!")

    def test_decode_default_mime(self):
        uri = "data:,Hello%2C%20World%21"
        result = self.manager.decode(uri)
        self.assertEqual(result["mime_type"], "text/plain;charset=US-ASCII")

    def test_decode_invalid_uri(self):
        with self.assertRaises(ValueError):
            self.manager.decode("http://example.com")

        with self.assertRaises(ValueError):
            self.manager.decode("data:text/plain;base64")

class TestRunDataUriLabLogic(unittest.TestCase):

    @patch("sys.stdout", new_callable=tempfile.SpooledTemporaryFile)
    def test_run_encode_text(self, mock_stdout):
        args = argparse.Namespace(
            action="encode",
            text="Hello",
            file=None,
            mime=None,
            no_base64=False
        )
        # Expected base64 for "Hello" is "SGVsbG8="
        with patch('builtins.print') as mock_print:
            success = run_data_uri_lab_logic(args)
            self.assertTrue(success)
            mock_print.assert_called_with("data:text/plain;base64,SGVsbG8=")

    @patch("sys.stdout", new_callable=tempfile.SpooledTemporaryFile)
    def test_run_decode(self, mock_stdout):
        args = argparse.Namespace(
            action="decode",
            uri="data:text/plain;base64,SGVsbG8=",
            output=None,
            info_only=False
        )
        with patch('builtins.print') as mock_print:
            success = run_data_uri_lab_logic(args)
            self.assertTrue(success)
            mock_print.assert_called_with("Hello")

    @patch('sys.exit', side_effect=SystemExit(0))
    def test_run_tui(self, mock_exit):
        mock_agent_tui = MagicMock()
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app

        args = argparse.Namespace(action="tui", project_dir=Path("."))

        mock_shared_tui = MagicMock()
        mock_shared_tui.AgentTUI = mock_agent_tui

        with patch.dict('sys.modules', {'shared.tui': mock_shared_tui}):
            with self.assertRaises(SystemExit):
                run_data_uri_lab_logic(args)

        mock_agent_tui.assert_called_once_with(project_dir=Path("."), start_tab="tab-data-uri")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()
