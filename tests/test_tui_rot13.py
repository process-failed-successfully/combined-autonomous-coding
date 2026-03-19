import unittest
from unittest.mock import MagicMock
from textual.widgets import TextArea
from shared.tui_rot13 import Rot13LabTab

class TestRot13LabTab(unittest.IsolatedAsyncioTestCase):
    async def test_mount(self):
        tab = Rot13LabTab()
        self.assertIsInstance(tab, Rot13LabTab)

    async def test_encode_decode_interaction(self):
        tab = Rot13LabTab()
        mock_app = MagicMock()
        type(tab).app = mock_app

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "Hello World!"
        mock_output = MagicMock(spec=TextArea)

        def query_one_side_effect(selector, type=None):
            if selector == "#rot13-input":
                return mock_input
            if selector == "#rot13-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Encode
        event = MagicMock()
        event.button.id = "btn-rot13-toggle"

        await tab.on_button_pressed(event)
        self.assertEqual(mock_output.text, "Uryyb Jbeyq!")
        mock_app.notify.assert_called_with("Applied ROT13.")

    async def test_swap_interaction(self):
        tab = Rot13LabTab()
        mock_app = MagicMock()
        type(tab).app = mock_app

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "Input"
        mock_output = MagicMock(spec=TextArea)
        mock_output.text = "Output"

        def query_one_side_effect(selector, type=None):
            if selector == "#rot13-input":
                return mock_input
            if selector == "#rot13-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Swap
        event = MagicMock()
        event.button.id = "btn-rot13-swap"

        await tab.on_button_pressed(event)
        self.assertEqual(mock_input.text, "Output")
        self.assertEqual(mock_output.text, "Input")
        mock_app.notify.assert_called_with("Swapped.")

    async def test_clear_interaction(self):
        tab = Rot13LabTab()
        mock_app = MagicMock()
        type(tab).app = mock_app

        mock_input = MagicMock(spec=TextArea)
        mock_input.text = "Input"
        mock_output = MagicMock(spec=TextArea)
        mock_output.text = "Output"

        def query_one_side_effect(selector, type=None):
            if selector == "#rot13-input":
                return mock_input
            if selector == "#rot13-output":
                return mock_output
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Clear
        event = MagicMock()
        event.button.id = "btn-rot13-clear"

        await tab.on_button_pressed(event)
        self.assertEqual(mock_input.text, "")
        self.assertEqual(mock_output.text, "")
        mock_app.notify.assert_called_with("Cleared.")

if __name__ == "__main__":
    unittest.main()
