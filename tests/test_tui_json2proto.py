import unittest
import asyncio
from unittest.mock import MagicMock
from shared.tui_json2proto import Json2ProtoLabTab
from textual.app import App
from textual.widgets import TextArea, Input

class DummyApp(App):
    def __init__(self):
        super().__init__()
        self.notifications = []

    def compose(self):
        yield Json2ProtoLabTab(id="tab")

    def notify(self, message, severity="information"):
        self.notifications.append({"message": message, "severity": severity})

class TestJson2ProtoLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_success(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one("#tab", Json2ProtoLabTab)
            json_input = app.query_one("#input-json", TextArea)
            root_input = app.query_one("#input-root-name", Input)
            output_area = app.query_one("#output-proto", TextArea)

            # Set input
            json_input.text = '{"name": "test"}'
            root_input.value = "User"

            # Trigger convert
            tab.action_convert()

            self.assertIn("message User {", output_area.text)
            self.assertIn("string name = 1;", output_area.text)
            self.assertEqual(app.notifications[-1]["message"], "Converted to Protobuf successfully.")

    async def test_convert_invalid_json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one("#tab", Json2ProtoLabTab)
            json_input = app.query_one("#input-json", TextArea)
            output_area = app.query_one("#output-proto", TextArea)

            # Set invalid JSON
            json_input.text = '{"name": "test"'

            # Trigger convert
            tab.action_convert()

            self.assertIn("// Error:", output_area.text)
            self.assertTrue(any("Error" in n["message"] for n in app.notifications))

    async def test_convert_empty_json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one("#tab", Json2ProtoLabTab)
            json_input = app.query_one("#input-json", TextArea)

            # Set empty JSON
            json_input.text = '   '

            # Trigger convert
            tab.action_convert()
            self.assertEqual(app.notifications[-1]["message"], "Error: JSON input is empty.")

if __name__ == '__main__':
    unittest.main()
