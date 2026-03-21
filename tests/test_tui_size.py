import unittest
from textual.app import App, ComposeResult
from textual.widgets import Input, Button, Static
from shared.tui_size import SizeLabTab

class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield SizeLabTab()

class TestSizeLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_size_lab_tui_render(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Check widgets exist
            self.assertIsNotNone(app.query_one("#input-parse-size"))
            self.assertIsNotNone(app.query_one("#btn-parse"))
            self.assertIsNotNone(app.query_one("#output-parse"))

            self.assertIsNotNone(app.query_one("#input-format-bytes"))
            self.assertIsNotNone(app.query_one("#select-format-type"))
            self.assertIsNotNone(app.query_one("#btn-format"))
            self.assertIsNotNone(app.query_one("#output-format"))

    async def test_size_lab_parse(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#input-parse-size", Input)
            input_widget.value = "1.5 GB"

            await app.query_one("SizeLabTab").handle_parse(None)

            output_widget = app.query_one("#output-parse", Static)
            content = str(output_widget.render())

            self.assertIn("1500000000", content)
            self.assertIn("Bytes:", content)

    async def test_size_lab_parse_error(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#input-parse-size", Input)
            input_widget.value = "invalid"

            await app.query_one("SizeLabTab").handle_parse(None)

            output_widget = app.query_one("#output-parse", Static)
            content = str(output_widget.render())

            self.assertIn("Error:", content)

    async def test_size_lab_format_iec(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#input-format-bytes", Input)
            input_widget.value = "2048"

            await app.query_one("SizeLabTab").handle_format(None)

            output_widget = app.query_one("#output-format", Static)
            content = str(output_widget.render())

            self.assertIn("2.00 KiB", content)

    async def test_size_lab_format_si(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_widget = app.query_one("#input-format-bytes", Input)
            input_widget.value = "2000"

            # Change select to SI
            select_widget = app.query_one("#select-format-type")
            select_widget.value = "si"

            await app.query_one("SizeLabTab").handle_format(None)

            output_widget = app.query_one("#output-format", Static)
            content = str(output_widget.render())

            self.assertIn("2.00 KB", content)

if __name__ == '__main__':
    unittest.main()
