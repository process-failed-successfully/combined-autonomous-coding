import unittest
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Static
from shared.tui_json_schema import JsonSchemaTab
import json


class DummyApp(App[str]):
    def compose(self) -> ComposeResult:
        yield JsonSchemaTab()


class TestTuiJsonSchema(unittest.IsolatedAsyncioTestCase):
    async def test_generate_schema_valid_json(self):
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            tab = app.query_one(JsonSchemaTab)
            input_widget = tab.query_one("#json-schema-input", TextArea)
            input_widget.text = '{"name": "test", "age": 25}'

            # Click generate
            await pilot.click("#btn-generate-json-schema")

            output_widget = tab.query_one("#json-schema-output", TextArea)
            status_widget = tab.query_one("#json-schema-status", Static)

            self.assertIn("Successfully generated JSON Schema", str(status_widget.render()))

            schema = json.loads(output_widget.text)
            self.assertEqual(schema["type"], "object")
            self.assertEqual(schema["properties"]["name"]["type"], "string")
            self.assertEqual(schema["properties"]["age"]["type"], "integer")

    async def test_generate_schema_invalid_json(self):
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            tab = app.query_one(JsonSchemaTab)
            input_widget = tab.query_one("#json-schema-input", TextArea)
            input_widget.text = '{"name": "test", "age": 25'  # Missing closing brace

            await pilot.click("#btn-generate-json-schema")

            output_widget = tab.query_one("#json-schema-output", TextArea)
            status_widget = tab.query_one("#json-schema-status", Static)

            self.assertIn("Invalid JSON", str(status_widget.render()))
            self.assertEqual(output_widget.text, "")

    async def test_clear_button(self):
        app = DummyApp()
        async with app.run_test(size=(200, 200)) as pilot:
            tab = app.query_one(JsonSchemaTab)
            input_widget = tab.query_one("#json-schema-input", TextArea)
            input_widget.text = '{"name": "test"}'

            await pilot.click("#btn-generate-json-schema")

            output_widget = tab.query_one("#json-schema-output", TextArea)
            self.assertNotEqual(output_widget.text, "")

            await pilot.click("#btn-clear-json-schema")

            self.assertEqual(input_widget.text, "")
            self.assertEqual(output_widget.text, "")
