import unittest
import pytest
import asyncio
from pathlib import Path
from textual.app import App

pytest.importorskip("textual")

from shared.tui_json2sql import Json2SqlTab

class DummyApp(App):
    def compose(self):
        yield Json2SqlTab(project_dir=Path("."))

class TestJson2SqlTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_button_success(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Json2SqlTab)

            # Setup inputs
            tab.input_area.text = '[{"id": 1, "name": "Test"}]'
            tab.table_input.value = "my_table"

            # Click convert
            await pilot.click("#btn-convert-json2sql")
            await pilot.pause()

            # Verify output
            self.assertEqual(tab.output_area.text, "INSERT INTO my_table (id, name) VALUES (1, 'Test');")

    async def test_convert_button_empty_json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Json2SqlTab)

            tab.input_area.text = "   "
            await pilot.click("#btn-convert-json2sql")
            await pilot.pause()

            self.assertIn("Error: Input JSON is empty", tab.output_area.text)

    async def test_convert_button_empty_table(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Json2SqlTab)

            tab.input_area.text = '[{"id": 1}]'
            tab.table_input.value = ""
            await pilot.click("#btn-convert-json2sql")
            await pilot.pause()

            self.assertIn("Error: Table name is required", tab.output_area.text)

if __name__ == '__main__':
    unittest.main()
