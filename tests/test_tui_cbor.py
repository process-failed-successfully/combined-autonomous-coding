import unittest
from unittest.mock import MagicMock
from textual.app import App
from shared.tui_cbor import CborTab


class DummyApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notifications = []

    def notify(self, message: str, *, title: str = "", severity: str = "information", timeout: float = 3.0) -> None:
        self.notifications.append({"message": message, "severity": severity})


class TestTuiCbor(unittest.IsolatedAsyncioTestCase):
    async def test_cbor_tab_encode(self):
        tab = CborTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        # We need to test process_data method, but mock the query_one part
        def mock_query_one(selector, *args, **kwargs):
            if selector == "#cbor-input":
                return type('TextArea', (), {'text': '{"a": 1}'})()
            elif selector == "#cbor-output":
                tab.output_area = type('TextArea', (), {'text': ''})()
                return tab.output_area
            elif selector == "#cbor-mode-radios":
                encode_btn = type('RadioButton', (), {'value': True})()
                decode_btn = type('RadioButton', (), {'value': False})()
                return type('RadioSet', (), {'children': [encode_btn, decode_btn]})()
            elif selector == "#cbor-out-format":
                return type('Select', (), {'value': 'hex'})()
            return MagicMock()

        tab.query_one = MagicMock(side_effect=mock_query_one)

        tab.process_data()

        self.assertIn("a1616101", tab.output_area.text)  # CBOR hex for {"a": 1}

    async def test_cbor_tab_decode(self):
        tab = CborTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        def mock_query_one(selector, *args, **kwargs):
            if selector == "#cbor-input":
                return type('TextArea', (), {'text': 'a1616101'})()
            elif selector == "#cbor-output":
                tab.output_area = type('TextArea', (), {'text': ''})()
                return tab.output_area
            elif selector == "#cbor-mode-radios":
                encode_btn = type('RadioButton', (), {'value': False})()
                decode_btn = type('RadioButton', (), {'value': True})()
                return type('RadioSet', (), {'children': [encode_btn, decode_btn]})()
            elif selector == "#cbor-in-format":
                return type('Select', (), {'value': 'hex'})()
            return MagicMock()

        tab.query_one = MagicMock(side_effect=mock_query_one)

        tab.process_data()

        self.assertIn('"a": 1', tab.output_area.text)

    def tearDown(self):
        if hasattr(CborTab, 'app'):
            delattr(CborTab, 'app')


if __name__ == '__main__':
    unittest.main()
