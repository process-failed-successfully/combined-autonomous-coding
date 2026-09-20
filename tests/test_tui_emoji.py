import pytest
from textual.app import App, ComposeResult
from textual.widgets import TabbedContent
from shared.tui_emoji import EmojiLabTab

class DummyApp(App):
    def compose(self) -> ComposeResult:
        with TabbedContent():
            yield EmojiLabTab()

@pytest.mark.asyncio
async def test_emoji_lab_tab():
    app = DummyApp()
    async with app.run_test(size=(120, 40)) as pilot:
        # Check if tab mounted correctly
        tab = app.query_one(EmojiLabTab)
        assert tab is not None

        # Test basic search functionality in UI
        input_widget = app.query_one("#input-emoji-search")
        input_widget.value = "rocket"

        # Call the search handler directly since pilot click is out of bounds
        tab.on_search()
        await pilot.pause()

        # Check datatable
        table = app.query_one("#table-emoji")
        assert table.row_count > 0

        # Call the random handler
        tab.on_random()
        await pilot.pause()
        assert table.row_count == 1

        # Call list all
        tab.on_list()
        await pilot.pause()
        assert table.row_count == 100
