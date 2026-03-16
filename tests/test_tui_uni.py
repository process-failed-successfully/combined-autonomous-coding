import pytest
from unittest.mock import MagicMock, patch
from shared.tui_uni import UniLabTab
from textual.app import App
from textual.widgets import Input, Button, DataTable, RichLog, Select

class DummyApp(App):
    def compose(self):
        yield UniLabTab()

@pytest.fixture
def app():
    return DummyApp()

@pytest.mark.asyncio
async def test_uni_lab_tab_mount(app):
    async with app.run_test() as pilot:
        tab = app.query_one(UniLabTab)
        assert tab is not None
        # Check all UI elements are present
        assert app.query_one("#uni-operation-select") is not None
        assert app.query_one("#uni-inspect-input") is not None
        assert app.query_one("#uni-inspect-btn") is not None
        assert app.query_one("#uni-inspect-table") is not None

        assert app.query_one("#uni-search-input") is not None
        assert app.query_one("#uni-search-limit") is not None
        assert app.query_one("#uni-search-btn") is not None
        assert app.query_one("#uni-search-table") is not None

        assert app.query_one("#uni-escape-input") is not None
        assert app.query_one("#uni-escape-btn") is not None
        assert app.query_one("#uni-escape-log") is not None

@pytest.mark.asyncio
@patch("shared.tui_uni.UniLabManager")
async def test_uni_lab_inspect(mock_manager_class, app):
    mock_manager = mock_manager_class.return_value
    mock_manager.inspect.return_value = [
        {"char": "A", "code_point": "U+0041", "category": "Lu", "utf8": "41", "name": "LATIN CAPITAL LETTER A"}
    ]

    async with app.run_test() as pilot:
        # Set operation to Inspect
        select = app.query_one("#uni-operation-select", Select)
        select.value = "Inspect"
        await pilot.pause()

        # Enter text
        app.query_one("#uni-inspect-input", Input).value = "A"

        # Manually trigger button press
        btn = app.query_one("#uni-inspect-btn", Button)
        btn.action_press()
        await pilot.pause()

        mock_manager.inspect.assert_called_once_with("A")

        # Check table
        table = app.query_one("#uni-inspect-table", DataTable)
        assert table.row_count == 1

@pytest.mark.asyncio
@patch("shared.tui_uni.UniLabManager")
async def test_uni_lab_search(mock_manager_class, app):
    mock_manager = mock_manager_class.return_value
    mock_manager.search.return_value = [
        {"char": "A", "code_point": "U+0041", "name": "LATIN CAPITAL LETTER A"}
    ]

    async with app.run_test() as pilot:
        # Set operation to Search
        select = app.query_one("#uni-operation-select", Select)
        select.value = "Search"
        await pilot.pause()

        # Enter query
        app.query_one("#uni-search-input", Input).value = "LATIN CAPITAL LETTER A"

        # Manually trigger button press
        btn = app.query_one("#uni-search-btn", Button)
        btn.action_press()
        await pilot.pause()

        mock_manager.search.assert_called_once_with("LATIN CAPITAL LETTER A", limit=50)

        # Check table
        table = app.query_one("#uni-search-table", DataTable)
        assert table.row_count == 1

@pytest.mark.asyncio
@patch("shared.tui_uni.UniLabManager")
async def test_uni_lab_escape(mock_manager_class, app):
    mock_manager = mock_manager_class.return_value
    mock_manager.escape.return_value = "\\u0041"

    async with app.run_test() as pilot:
        # Set operation to Escape
        select = app.query_one("#uni-operation-select", Select)
        select.value = "Escape"
        await pilot.pause()

        # Enter text
        app.query_one("#uni-escape-input", Input).value = "A"

        # Manually trigger button press
        btn = app.query_one("#uni-escape-btn", Button)
        btn.action_press()
        await pilot.pause()

        mock_manager.escape.assert_called_once_with("A")

        # Check log
        log = app.query_one("#uni-escape-log", RichLog)
        assert len(log.lines) > 0

@pytest.mark.asyncio
@patch("shared.tui_uni.UniLabManager")
async def test_uni_lab_unescape(mock_manager_class, app):
    mock_manager = mock_manager_class.return_value
    mock_manager.unescape.return_value = "A"

    async with app.run_test() as pilot:
        # Set operation to Unescape
        select = app.query_one("#uni-operation-select", Select)
        select.value = "Unescape"
        await pilot.pause()

        # Enter text
        app.query_one("#uni-escape-input", Input).value = "\\u0041"

        # Manually trigger button press
        btn = app.query_one("#uni-escape-btn", Button)
        btn.action_press()
        await pilot.pause()

        mock_manager.unescape.assert_called_once_with("\\u0041")

        # Check log
        log = app.query_one("#uni-escape-log", RichLog)
        assert len(log.lines) > 0
