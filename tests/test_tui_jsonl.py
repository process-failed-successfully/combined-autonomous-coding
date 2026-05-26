import unittest
from typing import Any
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Select, Static
from shared.tui_jsonl import JsonlLabTab

class DummyApp(App[Any]):
    def compose(self) -> ComposeResult:
        yield JsonlLabTab()

class TestTuiJsonl(unittest.IsolatedAsyncioTestCase):
    async def test_convert_json2jsonl(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(JsonlLabTab)
            action_select = tab.query_one("#jsonl-action-select", Select)
            input_ta = tab.query_one("#jsonl-input-ta", TextArea)
            output_ta = tab.query_one("#jsonl-output-ta", TextArea)
            status_static = tab.query_one("#jsonl-status", Static)

            action_select.value = "json2jsonl"
            input_ta.text = '[{"name": "Alice"}]'

            await pilot.click("#jsonl-run-btn")
            await pilot.pause()

            self.assertIn('{"name":"Alice"}', output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_convert_jsonl2json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(JsonlLabTab)
            action_select = tab.query_one("#jsonl-action-select", Select)
            input_ta = tab.query_one("#jsonl-input-ta", TextArea)
            output_ta = tab.query_one("#jsonl-output-ta", TextArea)
            status_static = tab.query_one("#jsonl-status", Static)

            action_select.value = "jsonl2json"
            input_ta.text = '{"name": "Alice"}'

            await pilot.click("#jsonl-run-btn")
            await pilot.pause()

            self.assertIn('"name": "Alice"', output_ta.text)
            self.assertIn("successful", str(status_static.render()))

    async def test_validate_valid_jsonl(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(JsonlLabTab)
            action_select = tab.query_one("#jsonl-action-select", Select)
            input_ta = tab.query_one("#jsonl-input-ta", TextArea)
            output_ta = tab.query_one("#jsonl-output-ta", TextArea)
            status_static = tab.query_one("#jsonl-status", Static)

            action_select.value = "validate"
            input_ta.text = '{"name": "Alice"}'

            await pilot.click("#jsonl-run-btn")
            await pilot.pause()

            self.assertEqual(output_ta.text, "Valid JSON Lines.")
            self.assertIn("Valid JSON Lines", str(status_static.render()))

    async def test_validate_invalid_jsonl(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(JsonlLabTab)
            action_select = tab.query_one("#jsonl-action-select", Select)
            input_ta = tab.query_one("#jsonl-input-ta", TextArea)
            output_ta = tab.query_one("#jsonl-output-ta", TextArea)
            status_static = tab.query_one("#jsonl-status", Static)

            action_select.value = "validate"
            input_ta.text = '{"name": "Alice"\n"invalid line"'

            await pilot.click("#jsonl-run-btn")
            await pilot.pause()

            self.assertIn("Invalid JSON", output_ta.text)
            self.assertIn("Invalid JSON", str(status_static.render()))

if __name__ == '__main__':
    unittest.main()
