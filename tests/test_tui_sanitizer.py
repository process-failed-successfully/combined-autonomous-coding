import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_sanitizer import SanitizerTab
from textual.widgets import RichLog, TextArea, Label, Button

class TestSanitizerTab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.tui_sanitizer.Sanitizer")
    def test_initialization(self, MockSanitizer):
        tab = SanitizerTab(self.project_dir)
        self.assertEqual(tab.project_dir, self.project_dir)
        # MockSanitizer is the class, tab.sanitizer is the instance
        self.assertTrue(isinstance(tab.sanitizer, MagicMock))

    @patch("shared.tui_sanitizer.Sanitizer")
    def test_check_text_pii_detected(self, MockSanitizer):
        # Setup mock sanitizer instance
        mock_sanitizer_instance = MockSanitizer.return_value
        mock_sanitizer_instance.check_text.return_value = ["EMAIL"]
        mock_sanitizer_instance.sanitize_text.return_value = "sanitized text"

        tab = SanitizerTab(self.project_dir)

        # Mock widgets
        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "test email@example.com"
        mock_log = MagicMock(spec=RichLog)

        # Mock query_one
        def query_one_side_effect(selector, type=None):
            if selector == "#san-text-input":
                return mock_input
            if selector == "#san-text-result":
                return mock_log
            raise ValueError(f"Unexpected selector: {selector}")

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Call check_text
        tab.check_text()

        # Verify interaction
        mock_sanitizer_instance.check_text.assert_called_with("test email@example.com")
        mock_sanitizer_instance.sanitize_text.assert_called_with("test email@example.com")

        # We can't strictly check exact calls due to possible formatting calls, but we check key interactions
        # mock_log.write should have been called with detection msg and sanitized text
        self.assertTrue(mock_log.write.called)
        # Check if sanitized text was written
        calls = [args[0] for args, kwargs in mock_log.write.call_args_list]
        self.assertIn("sanitized text", calls)

    @patch("shared.tui_sanitizer.Sanitizer")
    def test_check_file_clean(self, MockSanitizer):
        # Setup mock instance
        mock_sanitizer_instance = MockSanitizer.return_value
        mock_sanitizer_instance.sanitize_text.return_value = "content" # No change

        tab = SanitizerTab(self.project_dir)

        # Mock widgets
        mock_log = MagicMock(spec=RichLog)
        mock_lbl = MagicMock(spec=Label)
        mock_btn = MagicMock(spec=Button)

        def query_one_side_effect(selector, type=None):
            if selector == "#san-diff-log":
                return mock_log
            if selector == "#san-status-lbl":
                return mock_lbl
            if selector == "#btn-san-save":
                return mock_btn
            raise ValueError(f"Unexpected selector: {selector}")

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Mock Path
        mock_path = MagicMock(spec=Path)
        mock_path.read_text.return_value = "content"

        tab.check_file(mock_path)

        mock_log.write.assert_called_with("[green]No PII detected.[/green]")
        mock_lbl.update.assert_called_with("Clean.")
        self.assertEqual(mock_btn.disabled, True)

if __name__ == "__main__":
    unittest.main()
