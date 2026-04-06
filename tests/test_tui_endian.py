import unittest
from unittest.mock import MagicMock
from textual.widgets import Input, Select
from shared.tui_endian import EndianLabTab

class TestEndianLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tab = EndianLabTab()
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    def test_convert_hex(self):
        hex_in = MagicMock(spec=Input); hex_in.value = "0x11223344"
        hex_out = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#endian-hex-input": return hex_in
            if selector == "#endian-hex-output": return hex_out
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-endian-hex"

        self.tab.handle_button_pressed(event)
        self.assertEqual(hex_out.value, "44332211")
        self.tab.notify.assert_called_with("Converted.")

    def test_convert_hex_empty(self):
        hex_in = MagicMock(spec=Input); hex_in.value = ""
        hex_out = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#endian-hex-input": return hex_in
            if selector == "#endian-hex-output": return hex_out
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-endian-hex"

        self.tab.handle_button_pressed(event)
        self.tab.notify.assert_called_with("Input empty.", severity="warning")

    def test_convert_int(self):
        int_in = MagicMock(spec=Input); int_in.value = "4660"
        size_sel = MagicMock(spec=Select); size_sel.value = 2
        int_out = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#endian-int-input": return int_in
            if selector == "#endian-int-size": return size_sel
            if selector == "#endian-int-output": return int_out
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-endian-int"

        self.tab.handle_button_pressed(event)
        self.assertEqual(int_out.value, "13330")
        self.tab.notify.assert_called_with("Converted.")

    def test_convert_int_empty(self):
        int_in = MagicMock(spec=Input); int_in.value = ""
        size_sel = MagicMock(spec=Select); size_sel.value = 2
        int_out = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#endian-int-input": return int_in
            if selector == "#endian-int-size": return size_sel
            if selector == "#endian-int-output": return int_out
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-endian-int"

        self.tab.handle_button_pressed(event)
        self.tab.notify.assert_called_with("Input empty.", severity="warning")

    def test_convert_int_invalid(self):
        int_in = MagicMock(spec=Input); int_in.value = "abc"
        size_sel = MagicMock(spec=Select); size_sel.value = 2
        int_out = MagicMock(spec=Input)

        def query_side_effect(selector, type=None):
            if selector == "#endian-int-input": return int_in
            if selector == "#endian-int-size": return size_sel
            if selector == "#endian-int-output": return int_out
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        event = MagicMock()
        event.button.id = "btn-endian-int"

        self.tab.handle_button_pressed(event)
        self.tab.notify.assert_called_with("Invalid integer.", severity="error")

if __name__ == "__main__":
    unittest.main()
