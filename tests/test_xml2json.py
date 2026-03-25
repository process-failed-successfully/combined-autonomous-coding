import asyncio
import unittest
from typing import Any

from textual.app import App
from textual.widgets import TextArea

from shared.tui_xml2json import Xml2JsonTab
from shared.xml2json_lab import Xml2JsonManager


class TestXml2Json(unittest.TestCase):
    def setUp(self):
        self.manager = Xml2JsonManager()

    def test_xml2json_valid_simple(self):
        xml = "<root><item>Hello</item></root>"
        expected = {"root": {"item": "Hello"}}
        result = self.manager.convert_string(xml)
        self.assertEqual(result, expected)

    def test_xml2json_valid_attributes(self):
        xml = "<root id='1'><item>World</item></root>"
        expected = {"root": {"@attributes": {"id": "1"}, "item": "World"}}
        result = self.manager.convert_string(xml)
        self.assertEqual(result, expected)

    def test_xml2json_valid_lists(self):
        xml = "<root><item>One</item><item>Two</item></root>"
        expected = {"root": {"item": ["One", "Two"]}}
        result = self.manager.convert_string(xml)
        self.assertEqual(result, expected)

    def test_xml2json_invalid(self):
        xml = "<root><item>Hello</root>"
        with self.assertRaises(ValueError):
            self.manager.convert_string(xml)


class DummyApp(App[Any]):
    def compose(self):
        yield Xml2JsonTab()


class TestXml2JsonTui(unittest.IsolatedAsyncioTestCase):
    async def test_tui_render(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # Type something into the input
            await pilot.click("#xml2json-input")
            # Set the text attribute directly since it's a TextArea
            app.query_one("#xml2json-input", TextArea).text = "<root><item>Test</item></root>"
            await pilot.click("#btn-convert-xml2json")

            # Check the output
            # Need a slight pause for text generation
            await asyncio.sleep(0.1)

            output_area = app.query_one("#xml2json-output", TextArea)

            # Since JSON output comes out formatted
            self.assertIn('"item": "Test"', output_area.text)


if __name__ == '__main__':
    unittest.main()
