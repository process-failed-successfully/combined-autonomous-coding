import unittest
from unittest.mock import patch, MagicMock
from textual.widgets import Input, RadioSet, RadioButton
from shared.tui_case import CaseLabTab

class TestTuiCase(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = CaseLabTab()

    async def test_case_lab_tab_mount(self):
        """Test that CaseLabTab has required inputs."""
        self.assertIsNotNone(self.tab.manager)

    @patch("shared.tui_case.CaseLabTab.query_one")
    def test_case_lab_convert_camel(self, mock_query_one):
        """Test conversion success flow for camelCase."""
        mock_input = MagicMock(spec=Input)
        mock_input.value = "hello_world"

        mock_output = MagicMock(spec=Input)
        mock_output.value = ""

        mock_radio_set = MagicMock(spec=RadioSet)
        mock_radio_button = MagicMock(spec=RadioButton)
        mock_radio_button.id = "radio-camel"
        mock_radio_set.pressed_button = mock_radio_button

        def side_effect(selector, *args, **kwargs):
            if selector == "#case-input":
                return mock_input
            if selector == "#case-output":
                return mock_output
            if selector == "#case-format-radios":
                return mock_radio_set
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.convert_string()

        self.assertEqual(mock_output.value, "helloWorld")

    @patch("shared.tui_case.CaseLabTab.query_one")
    def test_case_lab_convert_snake(self, mock_query_one):
        """Test conversion success flow for snake_case."""
        mock_input = MagicMock(spec=Input)
        mock_input.value = "helloWorld"

        mock_output = MagicMock(spec=Input)
        mock_output.value = ""

        mock_radio_set = MagicMock(spec=RadioSet)
        mock_radio_button = MagicMock(spec=RadioButton)
        mock_radio_button.id = "radio-snake"
        mock_radio_set.pressed_button = mock_radio_button

        def side_effect(selector, *args, **kwargs):
            if selector == "#case-input":
                return mock_input
            if selector == "#case-output":
                return mock_output
            if selector == "#case-format-radios":
                return mock_radio_set
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.convert_string()

        self.assertEqual(mock_output.value, "hello_world")

    @patch("shared.tui_case.CaseLabTab.query_one")
    def test_case_lab_convert_empty(self, mock_query_one):
        """Test conversion flow when input is empty."""
        mock_input = MagicMock(spec=Input)
        mock_input.value = "   "

        mock_output = MagicMock(spec=Input)
        mock_output.value = "previousValue"

        mock_radio_set = MagicMock(spec=RadioSet)

        def side_effect(selector, *args, **kwargs):
            if selector == "#case-input":
                return mock_input
            if selector == "#case-output":
                return mock_output
            if selector == "#case-format-radios":
                return mock_radio_set
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.convert_string()

        self.assertEqual(mock_output.value, "")

    @patch("shared.tui_case.CaseLabTab.query_one")
    def test_case_lab_convert_no_radio_selected(self, mock_query_one):
        """Test conversion flow when no radio button is selected."""
        mock_input = MagicMock(spec=Input)
        mock_input.value = "hello world"

        mock_output = MagicMock(spec=Input)
        mock_output.value = "unchanged"

        mock_radio_set = MagicMock(spec=RadioSet)
        mock_radio_set.pressed_button = None

        def side_effect(selector, *args, **kwargs):
            if selector == "#case-input":
                return mock_input
            if selector == "#case-output":
                return mock_output
            if selector == "#case-format-radios":
                return mock_radio_set
            return MagicMock()

        mock_query_one.side_effect = side_effect

        self.tab.convert_string()

        self.assertEqual(mock_output.value, "unchanged")

if __name__ == "__main__":
    unittest.main()
