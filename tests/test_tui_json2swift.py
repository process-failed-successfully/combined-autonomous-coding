import pytest
import unittest
from unittest.mock import patch

import sys

try:
    from textual.app import App
    from textual.widgets import TextArea, Input, Static
    from shared.tui_json2swift import Json2SwiftLabTab
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = object  # Dummy to satisfy parser before skipif


@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
class DummyApp(App):
    def compose(self):
        yield Json2SwiftLabTab()

@pytest.mark.skipif(not TEXTUAL_AVAILABLE, reason="textual is not installed")
class TestJson2SwiftLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_convert_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#json2swift-input-ta", TextArea)
            input_ta.text = '{"name": "test"}'

            name_input = app.query_one("#json2swift-name-input", Input)
            name_input.value = "TestStruct"

            btn = app.query_one("#json2swift-convert-btn")
            event = unittest.mock.MagicMock()
            event.button.id = btn.id
            await app.query_one('Json2SwiftLabTab').on_button_pressed(event)

            output_ta = app.query_one("#json2swift-output-ta", TextArea)
            assert "struct TestStruct: Codable {" in output_ta.text
            assert "var name: String?" in output_ta.text

            status = app.query_one("#json2swift-status", Static)
            assert "Conversion successful" in str(status.render())

    async def test_empty_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            btn = app.query_one("#json2swift-convert-btn")
            event = unittest.mock.MagicMock()
            event.button.id = btn.id
            await app.query_one('Json2SwiftLabTab').on_button_pressed(event)

            status = app.query_one("#json2swift-status", Static)
            assert "Input is empty" in str(status.render())

    async def test_invalid_input_ui(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            input_ta = app.query_one("#json2swift-input-ta", TextArea)
            input_ta.text = '{"invalid":'

            btn = app.query_one("#json2swift-convert-btn")
            event = unittest.mock.MagicMock()
            event.button.id = btn.id
            await app.query_one('Json2SwiftLabTab').on_button_pressed(event)

            status = app.query_one("#json2swift-status", Static)
            assert "Error" in str(status.render())
