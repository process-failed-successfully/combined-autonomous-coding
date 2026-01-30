import unittest
from unittest.mock import MagicMock, patch
from shared.tui import TUIStream, ApiLabTab
from pathlib import Path


class TestTUIIntegration(unittest.TestCase):
    def test_tui_stream(self):
        mock_log = MagicMock()
        mock_app = MagicMock()
        stream = TUIStream(mock_log, mock_app)

        stream.write("  Indented Text\n")

        # Verify call_from_thread was called
        mock_app.call_from_thread.assert_called_once()
        args = mock_app.call_from_thread.call_args
        func, text = args[0]

        # Verify the function passed is mock_log.write
        # Verify text is rstripped (trailing newline removed) but indentation kept
        self.assertEqual(func, mock_log.write)
        self.assertEqual(text, "  Indented Text")

    @patch("shared.tui.ApiLabManager")
    def test_api_lab_tab_methods(self, mock_manager):
        tab = ApiLabTab(Path("."))

        # Check if run_fuzzer is defined
        self.assertTrue(hasattr(tab, "run_fuzzer"))
        self.assertTrue(callable(tab.run_fuzzer))

        # Check if on_button_pressed handles the new button
        # We can't easily call it because it's async and uses query_one,
        # but we can verify the method exists and we could inspect source if we wanted,
        # but for now ensuring the method exists is a good sanity check.
        self.assertTrue(hasattr(tab, "on_button_pressed"))


if __name__ == "__main__":
    unittest.main()
