import unittest
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button, Input
from shared.tui_csv2json import Csv2JsonTab
from typing import Any

class DummyCsv2JsonApp(App[Any]):
    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Csv2JsonTab()

class TestTuiCsv2Json(unittest.IsolatedAsyncioTestCase):
    async def test_tui_csv2json_render_and_convert(self):
        app = DummyCsv2JsonApp()
        async with app.run_test() as pilot:
            # 1. Verify initial state
            tab = app.query_one(Csv2JsonTab)
            self.assertIsNotNone(tab)

            input_area = app.query_one("#csv2json_input", TextArea)
            output_area = app.query_one("#csv2json_output", TextArea)
            delimiter_input = app.query_one("#csv2json_delimiter", Input)

            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")
            self.assertEqual(delimiter_input.value, ",")

            # 2. Test successful conversion
            input_area.text = "name,age,city\nAlice,30,New York"
            await pilot.click("#btn_convert")

            # Allow some time for processing
            await pilot.pause()

            # The output JSON should be pretty-printed
            expected_json = '[\n  {\n    "name": "Alice",\n    "age": "30",\n    "city": "New York"\n  }\n]'
            self.assertEqual(output_area.text, expected_json)

            # 3. Test custom delimiter
            input_area.text = "id;status\n1;active"
            delimiter_input.value = ";"
            await pilot.click("#btn_convert")

            await pilot.pause()
            expected_custom_json = '[\n  {\n    "id": "1",\n    "status": "active"\n  }\n]'
            self.assertEqual(output_area.text, expected_custom_json)

            # 4. Test clear button
            await pilot.click("#btn_clear")
            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")

if __name__ == "__main__":
    unittest.main()
