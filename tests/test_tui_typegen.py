import unittest
from textual.app import App, ComposeResult
from shared.tui_typegen import TypegenLabTab



class DummyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield TypegenLabTab()



class TestTypegenLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_tab_initialization(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            self.assertTrue(pilot.app.query_one(TypegenLabTab))
            self.assertEqual(pilot.app.query_one("#typegen-root-name").value, "Root")
            self.assertEqual(pilot.app.query_one("#typegen-lang").value, "typescript")

    async def test_generate_types(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = pilot.app.query_one("#typegen-json-input")
            json_input.text = '{"name": "John"}'

            await pilot.click("#btn-typegen-generate")

            output = pilot.app.query_one("#typegen-output")
            self.assertIn("export interface Root {", output.text)
            self.assertIn("name: string;", output.text)

            # Switch lang to python
            lang_select = pilot.app.query_one("#typegen-lang")
            lang_select.value = "python"

            await pilot.click("#btn-typegen-generate")
            self.assertIn("@dataclass", output.text)
            self.assertIn("class Root:", output.text)

    async def test_clear_button(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            await pilot.click("#btn-typegen-clear")
            self.assertEqual(pilot.app.query_one("#typegen-json-input").text, "")
            self.assertEqual(pilot.app.query_one("#typegen-output").text, "")

    async def test_invalid_json(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            json_input = pilot.app.query_one("#typegen-json-input")
            json_input.text = '{invalid}'

            await pilot.click("#btn-typegen-generate")

            log = pilot.app.query_one("#typegen-log")
            log_text = "\n".join(str(line.text) for line in log.lines)
            self.assertIn("Error parsing JSON", log_text)
