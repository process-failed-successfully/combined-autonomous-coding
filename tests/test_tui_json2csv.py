import unittest
import json
from textual.app import App
from shared.tui_json2csv import Json2CsvTab

class DummyApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notifications = []

    def notify(self, message: str, *, title: str = "", severity: str = "information", timeout: float = 3.0) -> None:
        self.notifications.append({"message": message, "severity": severity})

class TestTUIJson2Csv(unittest.IsolatedAsyncioTestCase):
    async def test_json2csv_tab_convert(self):
        tab = Json2CsvTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        tab.input_area = type('TextArea', (), {'text': ''})()
        tab.output_area = type('TextArea', (), {'text': ''})()

        # Test empty input
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_convert'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "error")
        self.assertIn("cannot be empty", tab._mock_app.notifications[-1]["message"])

        # Test invalid json
        tab.input_area.text = '{invalid json'
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_convert'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "error")

        # Test valid conversion
        tab.input_area.text = '{"name": "Alice", "age": 30}'

        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_convert'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "information")
        self.assertIn("Converted successfully", tab._mock_app.notifications[-1]["message"])

        self.assertIn("age,name", tab.output_area.text)
        self.assertIn("30,Alice", tab.output_area.text)

    async def test_json2csv_tab_clear(self):
        tab = Json2CsvTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        tab.input_area = type('TextArea', (), {'text': '{"name": "Alice"}'})()
        tab.output_area = type('TextArea', (), {'text': 'name\\r\\nAlice'})()

        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_clear'})})())
        self.assertEqual(tab.input_area.text, "")
        self.assertEqual(tab.output_area.text, "")

    def tearDown(self):
        if hasattr(Json2CsvTab, 'app'):
            delattr(Json2CsvTab, 'app')

if __name__ == '__main__':
    unittest.main()
