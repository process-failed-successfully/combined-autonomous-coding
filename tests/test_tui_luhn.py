import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from textual.widgets import Input, Label
from shared.tui_luhn import LuhnLabTab

class TestTuiLuhn(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = LuhnLabTab()

    async def test_luhn_lab_tab_mount(self):
        """Test that LuhnLabTab has required inputs."""
        # Simple test to check initialization
        self.assertIsNotNone(self.tab.manager)

    @patch("shared.tui_luhn.LuhnLabTab.query_one")
    def test_luhn_lab_validate_success(self, mock_query_one):
        """Test validation success flow."""
        mock_input = MagicMock(spec=Input)
        mock_input.value = "79927398713" # Valid number

        mock_label = MagicMock(spec=Label)

        def side_effect(selector, *args, **kwargs):
            if selector == "#luhn-validate-input":
                return mock_input
            if selector == "#luhn-validate-output":
                return mock_label
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.validate_number()

        mock_label.update.assert_called_once()
        args = mock_label.update.call_args[0][0]
        self.assertIn("✅", args)

    @patch("shared.tui_luhn.LuhnLabTab.query_one")
    def test_luhn_lab_validate_fail(self, mock_query_one):
        """Test validation failure flow."""
        mock_input = MagicMock(spec=Input)
        mock_input.value = "79927398714" # Invalid number

        mock_label = MagicMock(spec=Label)

        def side_effect(selector, *args, **kwargs):
            if selector == "#luhn-validate-input":
                return mock_input
            if selector == "#luhn-validate-output":
                return mock_label
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.validate_number()

        mock_label.update.assert_called_once()
        args = mock_label.update.call_args[0][0]
        self.assertIn("❌", args)

    @patch("shared.tui_luhn.LuhnLabTab.query_one")
    def test_luhn_lab_generate_success(self, mock_query_one):
        """Test generate success flow."""
        mock_length = MagicMock(spec=Input)
        mock_length.value = "10"

        mock_prefix = MagicMock(spec=Input)
        mock_prefix.value = "123"

        mock_label = MagicMock(spec=Label)

        def side_effect(selector, *args, **kwargs):
            if selector == "#luhn-generate-length":
                return mock_length
            if selector == "#luhn-generate-prefix":
                return mock_prefix
            if selector == "#luhn-generate-output":
                return mock_label
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.generate_number()

        mock_label.update.assert_called_once()
        args = mock_label.update.call_args[0][0]
        self.assertIn("✅", args)

    @patch("shared.tui_luhn.LuhnLabTab.query_one")
    def test_luhn_lab_generate_error(self, mock_query_one):
        """Test generate error flow (e.g. length <= prefix)."""
        mock_length = MagicMock(spec=Input)
        mock_length.value = "2"

        mock_prefix = MagicMock(spec=Input)
        mock_prefix.value = "123"

        mock_label = MagicMock(spec=Label)

        def side_effect(selector, *args, **kwargs):
            if selector == "#luhn-generate-length":
                return mock_length
            if selector == "#luhn-generate-prefix":
                return mock_prefix
            if selector == "#luhn-generate-output":
                return mock_label
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.generate_number()

        mock_label.update.assert_called_once()
        args = mock_label.update.call_args[0][0]
        self.assertIn("❌", args)

if __name__ == "__main__":
    unittest.main()
