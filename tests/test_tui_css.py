import unittest
from unittest.mock import patch, MagicMock
import asyncio
from textual.app import App
from shared.tui_css import CssLabTab
from shared.css_lab import CssLabManager

class DummyTextArea:
    def __init__(self, id):
        self.id = id
        self.text = ""

    def __get__(self, instance, owner):
        return self.text
    def __set__(self, instance, value):
        self.text = value

class TestCssLabTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = CssLabTab()
        self.input_area = DummyTextArea("css-input")
        self.output_area = DummyTextArea("css-output")

        def mock_query_one(selector, type=None):
            if selector == "#css-input": return self.input_area
            if selector == "#css-output": return self.output_area
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=mock_query_one)
        self.tab.notify = MagicMock()

    async def test_format(self):
        self.input_area.text = "body{color:red}"

        mock_event = MagicMock()
        mock_event.button.id = "btn-css-format"
        await self.tab.on_button_pressed(mock_event)

        self.assertEqual(self.output_area.text, "body {\n    color:red;\n}")

    async def test_minify(self):
        self.input_area.text = "body {\n    color:red;\n}"

        mock_event = MagicMock()
        mock_event.button.id = "btn-css-minify"
        await self.tab.on_button_pressed(mock_event)

        self.assertEqual(self.output_area.text, "body{color:red}")

    async def test_swap(self):
        self.input_area.text = "input"
        self.output_area.text = "output"

        mock_event = MagicMock()
        mock_event.button.id = "btn-css-swap"
        await self.tab.on_button_pressed(mock_event)

        self.assertEqual(self.input_area.text, "output")
        self.assertEqual(self.output_area.text, "input")

    async def test_clear(self):
        self.input_area.text = "input"
        self.output_area.text = "output"

        mock_event = MagicMock()
        mock_event.button.id = "btn-css-clear"
        await self.tab.on_button_pressed(mock_event)

        self.assertEqual(self.input_area.text, "")
        self.assertEqual(self.output_area.text, "")

if __name__ == '__main__':
    unittest.main()
