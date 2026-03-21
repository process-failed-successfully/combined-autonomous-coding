import unittest
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_csv2md import Csv2MdTab
from textual.widgets import TextArea


class DummyApp(App):
    def __init__(self):
        super().__init__()
        self.tab = Csv2MdTab(project_dir=Path("."))

    def compose(self) -> ComposeResult:
        yield self.tab


class TestCsv2MdTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_csv(self):
        app = DummyApp()
        async with app.run_test():
            input_area = app.query_one("#csv2md-input", TextArea)
            input_area.text = "A,B\n1,2"

            app.tab.convert_csv()

            output_area = app.query_one("#csv2md-output", TextArea)
            self.assertIn("| A | B |", output_area.text)

    async def test_clear_text(self):
        app = DummyApp()
        async with app.run_test():
            input_area = app.query_one("#csv2md-input", TextArea)
            output_area = app.query_one("#csv2md-output", TextArea)

            input_area.text = "A,B\n1,2"
            output_area.text = "| A | B |"

            app.tab.clear_text()

            self.assertEqual(input_area.text, "")
            self.assertEqual(output_area.text, "")


if __name__ == "__main__":
    unittest.main()
