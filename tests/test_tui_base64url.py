import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import TextArea
from shared.tui_base64url import Base64UrlLabTab


class TestBase64UrlLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_base64url.DevTools")
        self.MockDevTools = self.patcher.start()

        self.tab = Base64UrlLabTab()
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_process_encode(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "Hello"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#b64url-input":
                return input_area
            if selector == "#b64url-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        self.MockDevTools.base64url_encode.return_value = "SGVsbG8"

        self.tab.process(encode=True)

        self.MockDevTools.base64url_encode.assert_called_with("Hello")
        self.assertEqual(output_area.text, "SGVsbG8")
        self.tab.notify.assert_called_with("Done.")

    def test_process_decode(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "SGVsbG8"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#b64url-input":
                return input_area
            if selector == "#b64url-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        self.MockDevTools.base64url_decode.return_value = "Hello"

        self.tab.process(encode=False)

        self.MockDevTools.base64url_decode.assert_called_with("SGVsbG8")
        self.assertEqual(output_area.text, "Hello")
        self.tab.notify.assert_called_with("Done.")

    def test_process_decode_error(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "invalid_base64!!"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#b64url-input":
                return input_area
            if selector == "#b64url-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect
        self.MockDevTools.base64url_decode.return_value = "Error: Invalid Base64URL"

        self.tab.process(encode=False)

        self.MockDevTools.base64url_decode.assert_called_with("invalid_base64!!")
        self.assertEqual(output_area.text, "Error: Invalid Base64URL")
        self.tab.notify.assert_called_with("Operation failed.", severity="error")

    def test_swap_content(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "InputText"
        output_area = MagicMock(spec=TextArea)
        output_area.text = "OutputText"

        def query_side_effect(selector, type=None):
            if selector == "#b64url-input":
                return input_area
            if selector == "#b64url-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.swap_content()

        self.assertEqual(input_area.text, "OutputText")
        self.assertEqual(output_area.text, "InputText")
        self.tab.notify.assert_called_with("Swapped Input and Output.")

    def test_clear_content(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "InputText"
        output_area = MagicMock(spec=TextArea)
        output_area.text = "OutputText"

        def query_side_effect(selector, type=None):
            if selector == "#b64url-input":
                return input_area
            if selector == "#b64url-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.clear_content()

        self.assertEqual(input_area.text, "")
        self.assertEqual(output_area.text, "")
        self.tab.notify.assert_called_with("Cleared.")

    def test_process_empty_input(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = ""
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#b64url-input":
                return input_area
            if selector == "#b64url-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.process(encode=True)
        self.tab.notify.assert_called_with("Input is empty.", severity="warning")


if __name__ == "__main__":
    unittest.main()
