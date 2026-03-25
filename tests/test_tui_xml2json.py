import unittest
from typing import Any
from textual.app import App
from textual.widgets import TextArea, Label
from shared.tui_xml2json import Xml2JsonTab


class DummyApp(App[Any]):
    def compose(self):
        yield Xml2JsonTab()


class TestXml2JsonTab(unittest.IsolatedAsyncioTestCase):
    async def test_xml2json_convert_valid(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Xml2JsonTab)
            input_area = tab.query_one("#xml2json-input", TextArea)
            output_area = tab.query_one("#xml2json-output", TextArea)
            status_label = tab.query_one("#lbl-xml2json-status", Label)

            input_area.text = "<root>test</root>"
            await pilot.click("#btn-xml2json-convert")

            self.assertIn('"root"', str(output_area.text))
            self.assertIn('"test"', str(output_area.text))
            self.assertEqual(str(status_label.render()), "")

    async def test_xml2json_convert_invalid(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Xml2JsonTab)
            input_area = tab.query_one("#xml2json-input", TextArea)
            output_area = tab.query_one("#xml2json-output", TextArea)
            status_label = tab.query_one("#lbl-xml2json-status", Label)

            input_area.text = "<root>unclosed"
            await pilot.click("#btn-xml2json-convert")

            self.assertEqual(str(output_area.text), "")
            self.assertIn("Error: Invalid XML", str(status_label.render()))

    async def test_xml2json_clear(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(Xml2JsonTab)
            input_area = tab.query_one("#xml2json-input", TextArea)
            output_area = tab.query_one("#xml2json-output", TextArea)
            status_label = tab.query_one("#lbl-xml2json-status", Label)

            input_area.text = "<root>test</root>"
            await pilot.click("#btn-xml2json-convert")
            self.assertIn('"root"', str(output_area.text))

            await pilot.click("#btn-xml2json-clear")
            self.assertEqual(str(input_area.text), "")
            self.assertEqual(str(output_area.text), "")
            self.assertEqual(str(status_label.render()), "")


if __name__ == '__main__':
    unittest.main()
