import pytest
from unittest.mock import MagicMock
from textual.app import App, ComposeResult
from textual.widgets import TabbedContent
from shared.tui_flatten import FlattenLabTab

class FlattenLabTestApp(App):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            yield FlattenLabTab()

@pytest.mark.asyncio
async def test_flatten_lab_tab_flatten_success():
    app = FlattenLabTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(FlattenLabTab)

        nested_ta = tab.query_one("#nested-json")
        flat_ta = tab.query_one("#flat-json")

        # Test Flatten
        nested_ta.text = '{"a": {"b": 2}}'
        btn_flatten = tab.query_one("#btn-flatten")

        event = MagicMock()
        event.button.id = btn_flatten.id
        tab.on_button_pressed(event)
        await pilot.pause()

        assert '"a.b": 2' in flat_ta.text

@pytest.mark.asyncio
async def test_flatten_lab_tab_unflatten_success():
    app = FlattenLabTestApp()
    async with app.run_test() as pilot:
        tab = app.query_one(FlattenLabTab)

        nested_ta = tab.query_one("#nested-json")
        flat_ta = tab.query_one("#flat-json")

        # Test Unflatten
        flat_ta.text = '{"a.b": 3}'
        btn_unflatten = tab.query_one("#btn-unflatten")

        event = MagicMock()
        event.button.id = btn_unflatten.id
        tab.on_button_pressed(event)
        await pilot.pause()

        assert '"a": {' in nested_ta.text
        assert '"b": 3' in nested_ta.text
