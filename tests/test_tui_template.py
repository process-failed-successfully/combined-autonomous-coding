import unittest
from pathlib import Path
from textual.app import App
from shared.tui_template import TemplateLabTab
from textual.widgets import TextArea, RichLog


class DummyApp(App):
    def __init__(self, tab, **kwargs):
        super().__init__(**kwargs)
        self.tab = tab

    def compose(self):
        yield self.tab


class TestTemplateLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_template_lab_tab(self):
        tab = TemplateLabTab(project_dir=Path("."))
        app = DummyApp(tab)
        async with app.run_test() as pilot:
            template_input = app.query_one("#template-input", TextArea)
            data_input = app.query_one("#template-data-input", TextArea)
            log = app.query_one("#template-results-log", RichLog)

            template_input.text = "Hello {{ name }}!"
            data_input.text = '{"name": "World"}'

            await pilot.pause(0.5)

            found = False
            for line in log.lines:
                if hasattr(line, "text") and "Hello World!" in line.text:
                    found = True
                    break
            self.assertTrue(found, "Template output 'Hello World!' not found in log")

    async def test_template_lab_invalid_json(self):
        tab = TemplateLabTab(project_dir=Path("."))
        app = DummyApp(tab)
        async with app.run_test() as pilot:
            template_input = app.query_one("#template-input", TextArea)
            data_input = app.query_one("#template-data-input", TextArea)
            log = app.query_one("#template-results-log", RichLog)

            template_input.text = "Hello {{ name }}!"
            # This is definitely invalid JSON and YAML map
            data_input.text = '{"name": "World", ]}'

            await pilot.pause(0.5)

            found = False
            for line in log.lines:
                text_content = getattr(line, "text", str(line))
                if "Invalid Data" in text_content:
                    found = True
                    break
            self.assertTrue(found, f"Error 'Invalid Data' not found in log. Actual lines: {log.lines}")


if __name__ == "__main__":
    unittest.main()
