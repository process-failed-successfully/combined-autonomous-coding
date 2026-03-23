import unittest
import json
from textual.app import App
from shared.tui_csv2json import Csv2JsonTab


class DummyApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notifications = []

    def notify(self, message: str, *, title: str = "", severity: str = "information", timeout: float = 3.0) -> None:
        self.notifications.append({"message": message, "severity": severity})


class TestTUICsv2Json(unittest.IsolatedAsyncioTestCase):
    async def test_csv2json_tab_convert(self):
        tab = Csv2JsonTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        tab.input_area = type('TextArea', (), {'text': ''})()
        tab.output_area = type('TextArea', (), {'text': ''})()

        # Test empty input
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_convert'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "error")
        self.assertIn("cannot be empty", tab._mock_app.notifications[-1]["message"])

        # Test valid conversion
        tab.input_area.text = 'name,age\nAlice,30\nBob,25'

        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_convert'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "information")
        self.assertIn("Converted successfully", tab._mock_app.notifications[-1]["message"])

        parsed_output = json.loads(tab.output_area.text)
        self.assertEqual(len(parsed_output), 2)
        self.assertEqual(parsed_output[0]["name"], "Alice")
        self.assertEqual(parsed_output[0]["age"], "30")
        self.assertEqual(parsed_output[1]["name"], "Bob")
        self.assertEqual(parsed_output[1]["age"], "25")

    async def test_csv2json_tab_clear(self):
        tab = Csv2JsonTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        tab.input_area = type('TextArea', (), {'text': 'name\nAlice'})()
        tab.output_area = type('TextArea', (), {'text': '[\n  {\n    "name": "Alice"\n  }\n]'})()

        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_clear'})})())
        self.assertEqual(tab.input_area.text, "")
        self.assertEqual(tab.output_area.text, "")

    def tearDown(self):
        if hasattr(Csv2JsonTab, 'app'):
            delattr(Csv2JsonTab, 'app')


if __name__ == '__main__':
    unittest.main()
