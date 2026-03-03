import unittest
import json
from textual.app import App
from shared.tui_schema import SchemaLabTab


class DummyApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notifications = []

    def notify(self, message: str, *, title: str = "", severity: str = "information", timeout: float = 3.0) -> None:
        self.notifications.append({"message": message, "severity": severity})


class TestTUISchema(unittest.IsolatedAsyncioTestCase):
    async def test_schema_lab_tab_infer(self):
        tab = SchemaLabTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        tab.input_area = type('TextArea', (), {'text': ''})()
        tab.output_area = type('TextArea', (), {'text': ''})()
        tab.root_name_input = type('Input', (), {'value': 'Root'})()

        # Test empty input
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_infer'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "error")
        self.assertIn("cannot be empty", tab._mock_app.notifications[-1]["message"])

        # Test invalid json/yaml
        tab.input_area.text = '{invalid json'
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_infer'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "error")

        # Test valid infer
        tab.input_area.text = '{"name": "test", "age": 25}'

        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_infer'})})())
        self.assertEqual(tab._mock_app.notifications[-1]["severity"], "information")
        self.assertIn("inferred successfully", tab._mock_app.notifications[-1]["message"])

        output_schema = json.loads(tab.output_area.text)
        self.assertEqual(output_schema["type"], "object")
        self.assertEqual(output_schema["properties"]["name"]["type"], "string")
        self.assertEqual(output_schema["properties"]["age"]["type"], "integer")

    async def test_schema_lab_tab_convert(self):
        tab = SchemaLabTab()
        type(tab).app = property(lambda self: getattr(self, '_mock_app'))
        tab._mock_app = DummyApp()

        tab.input_area = type('TextArea', (), {'text': '{"type": "object", "properties": {"name": {"type": "string"}}}'})()
        tab.output_area = type('TextArea', (), {'text': ''})()
        tab.root_name_input = type('Input', (), {'value': 'TestRoot'})()

        # Test TS conversion
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_to_ts'})})())
        self.assertIn("Converted to TypeScript", tab._mock_app.notifications[-1]["message"])
        self.assertIn("export interface TestRoot", tab.output_area.text)
        self.assertIn("name: string;", tab.output_area.text)

        # Test Pydantic conversion
        await tab.on_button_pressed(type('Event', (), {'button': type('Button', (), {'id': 'btn_to_pydantic'})})())
        self.assertIn("Converted to Pydantic", tab._mock_app.notifications[-1]["message"])
        self.assertIn("class TestRoot(BaseModel):", tab.output_area.text)
        self.assertIn("name: Optional[str] = None", tab.output_area.text)

    def tearDown(self):
        if hasattr(SchemaLabTab, 'app'):
            delattr(SchemaLabTab, 'app')


if __name__ == '__main__':
    unittest.main()
