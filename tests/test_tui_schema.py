import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Mock knowledge manager dependency
sys.modules['shared.knowledge_graph'] = MagicMock()
sys.modules['shared.tui_knowledge_graph'] = MagicMock()

from shared.tui_schema import SchemaLabTab
from textual.widgets import TextArea, Select, TabbedContent
from textual.app import App, ComposeResult

# Create a minimal app to test the tab in isolation
class SchemaLabApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        with TabbedContent(id="tabs"):
            yield SchemaLabTab(self.project_dir)

class TestSchemaLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/mock_project")
        self.app = SchemaLabApp(project_dir=self.project_dir)

    async def test_schema_lab_tab_infer(self):
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(SchemaLabTab)
            self.assertIsNotNone(tab)

            # Test Infer
            infer_input = tab.query_one("#infer-input", TextArea)
            infer_input.text = '{"name": "test", "age": 25}'

            # Simulate click
            btn_infer = tab.query_one("#btn-infer")
            btn_infer.press()
            await pilot.pause()

            infer_output = tab.query_one("#infer-output", TextArea)
            self.assertIn('"type": "object"', infer_output.text)
            self.assertIn('"name"', infer_output.text)
            self.assertIn('"string"', infer_output.text)

    async def test_schema_lab_tab_convert(self):
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(SchemaLabTab)

            # Switch to convert tab
            tab.query_one("#tabs").active = "tab-convert"
            await pilot.pause()

            # Test Convert
            convert_input = tab.query_one("#convert-input", TextArea)
            convert_input.text = '{"type": "object", "properties": {"name": {"type": "string"}}}'

            # Default target is TypeScript Interface
            btn_convert = tab.query_one("#btn-convert")
            btn_convert.press()
            await pilot.pause()

            convert_output = tab.query_one("#convert-output", TextArea)
            self.assertIn("export interface RootInterface", convert_output.text)
            self.assertIn("name: string;", convert_output.text)

            # Switch to Pydantic Model
            target_select = tab.query_one("#convert-target", Select)
            target_select.value = "Pydantic Model"
            btn_convert.press()
            await pilot.pause()

            self.assertIn("class RootModel(BaseModel):", convert_output.text)
            self.assertIn("name: Optional[str] = None", convert_output.text)

if __name__ == '__main__':
    unittest.main()
