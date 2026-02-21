import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import TextArea, Select
from shared.tui_codec import CodecLabTab


class TestCodecLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_codec.CodecLabManager")
        self.MockManager = self.patcher.start()

        self.tab = CodecLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_process_encode_base64(self):
        # Mock inputs
        input_area = MagicMock(spec=TextArea)
        input_area.text = "Hello"
        output_area = MagicMock(spec=TextArea)
        select = MagicMock(spec=Select)
        select.value = "Base64"

        def query_side_effect(selector, type=None):
            if selector == "#codec-input":
                return input_area
            if selector == "#codec-output":
                return output_area
            if selector == "#codec-algo":
                return select
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.base64_encode.return_value = "SGVsbG8="

        self.tab.process(encode=True)

        self.mock_manager.base64_encode.assert_called_with("Hello")
        self.assertEqual(output_area.text, "SGVsbG8=")
        self.tab.notify.assert_called_with("Done.")

    def test_process_decode_hex_error(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "ZZ"
        output_area = MagicMock(spec=TextArea)
        select = MagicMock(spec=Select)
        select.value = "Hex"

        def query_side_effect(selector, type=None):
            if selector == "#codec-input":
                return input_area
            if selector == "#codec-output":
                return output_area
            if selector == "#codec-algo":
                return select
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.hex_decode.return_value = "Error: Invalid Hex"

        self.tab.process(encode=False)

        self.mock_manager.hex_decode.assert_called_with("ZZ")
        self.assertEqual(output_area.text, "Error: Invalid Hex")
        self.tab.notify.assert_called_with("Operation failed.", severity="error")

    def test_swap_content(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "Input"
        output_area = MagicMock(spec=TextArea)
        output_area.text = "Output"

        def query_side_effect(selector, type=None):
            if selector == "#codec-input":
                return input_area
            if selector == "#codec-output":
                return output_area
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.tab.swap_content()

        self.assertEqual(input_area.text, "Output")
        self.assertEqual(output_area.text, "Input")
        self.tab.notify.assert_called_with("Swapped Input and Output.")


if __name__ == "__main__":
    unittest.main()
