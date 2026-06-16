import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import TextArea, Button
from shared.tui_bencode import BencodeLabTab


class TestBencodeLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tab = BencodeLabTab()
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    def test_encode_empty(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = ""
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-encode"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertEqual(output_area.text, "Error: Please enter JSON string to encode.")

    def test_encode_success(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = '{"hello": "world"}'
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-encode"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertEqual(output_area.text, "d5:hello5:worlde")

    def test_encode_error(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = 'invalid json'
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-encode"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertTrue(output_area.text.startswith("❌ Input must be valid JSON:"))

    def test_decode_empty(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = ""
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-decode"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertEqual(output_area.text, "Error: Please enter Bencode string to decode.")

    def test_decode_success(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "d5:hello5:worlde"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-decode"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertEqual(output_area.text, '{\n  "hello": "world"\n}')

    def test_decode_error(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "invalid bencode"
        output_area = MagicMock(spec=TextArea)

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-decode"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertTrue(output_area.text.startswith("❌ Error decoding Bencode:"))

    def test_clear_content(self):
        input_area = MagicMock(spec=TextArea)
        input_area.text = "test"
        output_area = MagicMock(spec=TextArea)
        output_area.text = "test"

        def query_side_effect(selector, type=None):
            if selector == "#bencode-input":
                return input_area
            if selector == "#bencode-output":
                return output_area
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        btn = MagicMock(spec=Button)
        btn.id = "btn-clear"
        event = MagicMock()
        event.button = btn

        self.tab.on_button_pressed(event)

        self.assertEqual(input_area.text, "")
        self.assertEqual(output_area.text, "")


if __name__ == "__main__":
    unittest.main()
