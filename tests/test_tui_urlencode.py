import unittest
from unittest.mock import MagicMock
from textual.widgets import TextArea
from shared.tui_urlencode import UrlEncodeLabTab


class TestUrlEncodeLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tab = UrlEncodeLabTab()
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    def test_process_encode(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "hello world/&?"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#urlencode-input":
                return input_area
            if selector == "#urlencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.process(encode=True)

        self.assertEqual(output_area.text, "hello%20world/%26%3F")
        self.tab.notify.assert_called_with("Done.")

    def test_process_decode(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "hello%20world/%26%3F"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#urlencode-input":
                return input_area
            if selector == "#urlencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.process(encode=False)

        self.assertEqual(output_area.text, "hello world/&?")
        self.tab.notify.assert_called_with("Done.")

    def test_process_decode_error(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "invalid_base64!!"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#urlencode-input":
                return input_area
            if selector == "#urlencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # urllib.parse.unquote doesn't actually raise on invalid URL encoding, it just returns it or best effort.
        # So we mock it to raise an exception.
        import urllib.parse
        original_unquote = urllib.parse.unquote
        def mock_unquote(text):
            raise ValueError("Mock Error")

        urllib.parse.unquote = mock_unquote
        try:
            self.tab.process(encode=False)
        finally:
            urllib.parse.unquote = original_unquote

        self.assertEqual(output_area.text, "Error: Mock Error")
        self.tab.notify.assert_called_with("Exception: Mock Error", severity="error")

    def test_swap_content(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "InputText"
        output_area = MagicMock(spec=TextArea)
        output_area.text = "OutputText"

        def query_side_effect(selector, type=None):
            if selector == "#urlencode-input":
                return input_area
            if selector == "#urlencode-output":
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
            if selector == "#urlencode-input":
                return input_area
            if selector == "#urlencode-output":
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
            if selector == "#urlencode-input":
                return input_area
            if selector == "#urlencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.process(encode=True)
        self.tab.notify.assert_called_with("Input is empty.", severity="warning")


if __name__ == "__main__":
    unittest.main()
