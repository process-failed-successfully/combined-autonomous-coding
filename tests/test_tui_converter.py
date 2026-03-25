import pytest
from textual.app import App, ComposeResult
from textual.widgets import TextArea, Button, Select, RichLog, TabbedContent
from shared.tui_converter import ConverterLabTab
from pathlib import Path
from unittest.mock import MagicMock, patch

class ConverterApp(App):
    def compose(self) -> ComposeResult:
        yield ConverterLabTab(project_dir=Path("."))

@pytest.mark.asyncio
async def test_tui_converter_curl():
    app = ConverterApp()
    async with app.run_test() as pilot:
        # Initial tab is Curl
        inp = app.query_one("#curl-input", TextArea)
        inp.text = "curl http://example.com"

        await pilot.click("#btn-curl-convert")

        out = app.query_one("#curl-output", TextArea)
        assert "import requests" in out.text
        assert "http://example.com" in out.text

@pytest.mark.asyncio
async def test_tui_converter_types():
    app = ConverterApp()
    async with app.run_test() as pilot:
        # Switch tab
        tabs = app.query_one("#tabs", TabbedContent)
        tabs.active = "tab-types"
        await pilot.pause() # Wait for switch

        inp = app.query_one("#type-input", TextArea)
        inp.text = '{"name": "test"}'

        await pilot.click("#btn-type-convert")

        out = app.query_one("#type-output", TextArea)
        assert "class RootModel(BaseModel):" in out.text
        assert "name: str" in out.text

@pytest.mark.asyncio
async def test_tui_converter_format():
    app = ConverterApp()
    async with app.run_test() as pilot:
        tabs = app.query_one("#tabs", TabbedContent)
        tabs.active = "tab-format"
        await pilot.pause()

        inp = app.query_one("#fmt-input", TextArea)
        inp.text = '{"key": "value"}'

        # Default is JSON -> YAML
        await pilot.click("#btn-fmt-convert")

        out = app.query_one("#fmt-output", TextArea)
        assert "key: value" in out.text

@pytest.mark.asyncio
async def test_tui_converter_clear():
    app = ConverterApp()
    async with app.run_test() as pilot:
        inp = app.query_one("#curl-input", TextArea)
        inp.text = "something"
        out = app.query_one("#curl-output", TextArea)
        out.text = "result"

        await pilot.click("#btn-curl-clear")

        assert inp.text == ""
        assert out.text == ""
