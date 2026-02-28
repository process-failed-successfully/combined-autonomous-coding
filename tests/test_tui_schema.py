import unittest
import pytest
from pathlib import Path
from textual.app import App
from shared.tui_schema import SchemaLabTab
from textual.widgets import TextArea

class SchemaLabApp(App):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir
        self.tab = SchemaLabTab(project_dir)

    def compose(self):
        yield self.tab

class TestSchemaLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_schema_lab_tab_inference(self):
        project_dir = Path("/tmp/test_project")
        app = SchemaLabApp(project_dir)

        async with app.run_test() as pilot:
            # Type some valid JSON into the input
            input_text = '{"name": "Alice", "age": 30}'

            # Access the input area
            input_area = app.query_one("#schema-input", TextArea)
            input_area.text = input_text

            # Click the process button
            await pilot.click("#btn-schema-process")
            await pilot.pause(0.1)

            # Check outputs
            json_output = app.query_one("#schema-output-json", TextArea).text
            ts_output = app.query_one("#schema-output-ts", TextArea).text
            pydantic_output = app.query_one("#schema-output-pydantic", TextArea).text

            self.assertIn('"type": "object"', json_output)
            self.assertIn('export interface Root', ts_output)
            self.assertIn('class Root(BaseModel):', pydantic_output)
            self.assertIn('name', json_output)
            self.assertIn('age', json_output)

    async def test_schema_lab_tab_clear(self):
        project_dir = Path("/tmp/test_project")
        app = SchemaLabApp(project_dir)

        async with app.run_test() as pilot:
            input_area = app.query_one("#schema-input", TextArea)
            input_area.text = "test"

            await pilot.click("#btn-schema-clear")
            await pilot.pause(0.1)

            self.assertEqual(input_area.text, "")

if __name__ == "__main__":
    unittest.main()
