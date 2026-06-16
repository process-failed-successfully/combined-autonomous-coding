import unittest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea, TabbedContent
from shared.tui_converter import ConverterLabTab
from pathlib import Path


class ConverterApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield ConverterLabTab(project_dir=Path("."))


class TestTuiConverter(unittest.IsolatedAsyncioTestCase):
    async def test_tui_converter_curl(self):
        app = ConverterApp()
        async with app.run_test() as pilot:
            # Initial tab is Curl
            inp = app.query_one("#curl-input", TextArea)
            inp.text = "curl http://example.com"

            pilot.app.query_one("#btn-curl-convert").press()
            await pilot.pause()

            out = app.query_one("#curl-output", TextArea)
            self.assertIn("import requests", out.text)
            self.assertIn("http://example.com", out.text)

    async def test_tui_converter_types(self):
        app = ConverterApp()
        async with app.run_test() as pilot:
            # Switch tab
            tabs = app.query_one("#tabs", TabbedContent)
            tabs.active = "tab-types"
            await pilot.pause() # Wait for switch

            inp = app.query_one("#type-input", TextArea)
            inp.text = '{"name": "test"}'

            pilot.app.query_one("#btn-type-convert").press()
            await pilot.pause()

            out = app.query_one("#type-output", TextArea)
            self.assertIn("class RootModel(BaseModel):", out.text)
            self.assertIn("name: str", out.text)

    async def test_tui_converter_format(self):
        app = ConverterApp()
        async with app.run_test() as pilot:
            tabs = app.query_one("#tabs", TabbedContent)
            tabs.active = "tab-format"
            await pilot.pause()

            inp = app.query_one("#fmt-input", TextArea)
            inp.text = '{"key": "value"}'

            # Default is JSON -> YAML
            pilot.app.query_one("#btn-fmt-convert").press()
            await pilot.pause()

            out = app.query_one("#fmt-output", TextArea)
            self.assertIn("key: value", out.text)

    async def test_tui_converter_clear(self):
        app = ConverterApp()
        async with app.run_test() as pilot:
            inp = app.query_one("#curl-input", TextArea)
            inp.text = "something"
            out = app.query_one("#curl-output", TextArea)
            out.text = "result"

            pilot.app.query_one("#btn-curl-clear").press()
            await pilot.pause()

            self.assertEqual(inp.text, "")
            self.assertEqual(out.text, "")

if __name__ == '__main__':
    unittest.main()
