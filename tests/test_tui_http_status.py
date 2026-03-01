import unittest
from textual.app import App, ComposeResult
from textual.widgets import Input, DataTable, Label
from textual.containers import Vertical
from shared.tui_http_status import HttpStatusLabTab


class DummyApp(App):
    def compose(self) -> ComposeResult:
        yield HttpStatusLabTab()


class TestHttpStatusLabTui(unittest.IsolatedAsyncioTestCase):
    async def test_tui_initial_render(self):
        app = DummyApp()
        async with app.run_test():
            tab = app.query_one(HttpStatusLabTab)

            # Verify input exists
            search_input = tab.query_one("#http-status-search", Input)
            self.assertIsNotNone(search_input)

            # Verify table has content (all status codes)
            table = tab.query_one("#http-status-table", DataTable)
            self.assertGreater(len(table.rows), 50)

            # Verify details container is hidden initially
            details = tab.query_one("#http-status-details", Vertical)
            self.assertTrue(details.has_class("hidden"))

    async def test_tui_search_filtering(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(HttpStatusLabTab)

            search_input = tab.query_one("#http-status-search", Input)
            table = tab.query_one("#http-status-table", DataTable)

            # Set search query
            search_input.value = "teapot"
            await pilot.pause()

            # Should filter down to 1 result
            self.assertEqual(len(table.rows), 1)

            row_key = list(table.rows.keys())[0]
            # Since enter doesn't reliably trigger RowSelected in the test framework,
            # we directly post the message or call the handler
            # In Textual 0.x, RowSelected has a cursor_row argument
            tab.on_data_table_row_selected(DataTable.RowSelected(data_table=table, row_key=row_key, cursor_row=0))
            await pilot.pause()

            # Details should become visible and contain right info
            details = tab.query_one("#http-status-details", Vertical)
            self.assertFalse(details.has_class("hidden"))

            code_label = tab.query_one("#detail-code-message", Label)
            self.assertIn("418", str(code_label.render()))
            self.assertIn("teapot", str(code_label.render()))


if __name__ == "__main__":
    unittest.main()
