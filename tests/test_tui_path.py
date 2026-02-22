import unittest
from textual.app import App, ComposeResult
from shared.tui_path import PathLabTab
from textual.widgets import Input, Button, DataTable, Label, RichLog, TabbedContent

class PathLabApp(App):
    def compose(self) -> ComposeResult:
        yield PathLabTab()

class TestPathLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_mount_and_interact(self):
        app = PathLabApp()
        async with app.run_test(size=(120, 40)) as pilot:
            # Check if tab is mounted
            tab = app.query_one(PathLabTab)
            self.assertIsNotNone(tab)

            # Test Analysis
            inp = app.query_one("#path-insp-input", Input)
            inp.value = "test_file.txt"

            # Wait for layout
            await pilot.pause()

            btn = app.query_one("#btn-path-analyze", Button)
            self.assertTrue(btn.visible)

            # Trigger via method
            await tab.on_button_pressed(Button.Pressed(btn))

            # Wait for reaction
            await pilot.pause()

            table = app.query_one("#path-insp-table", DataTable)
            # Row count should be > 0
            self.assertGreater(len(table.rows), 0)

            # Test Relative Calc
            # Switch to Calculator Tab
            tabs = app.query_one(TabbedContent)
            tabs.active = "path-tab-calc"
            await pilot.pause()

            target_inp = app.query_one("#path-rel-target", Input)
            start_inp = app.query_one("#path-rel-start", Input)
            target_inp.value = "/a/b/c"
            start_inp.value = "/a"

            btn_rel = app.query_one("#btn-path-rel", Button)
            await tab.on_button_pressed(Button.Pressed(btn_rel))
            await pilot.pause()

            lbl = app.query_one("#lbl-path-rel-result", Label)
            # In Textual 8.0.0, to get the text, we can render it to string
            # or try checking internal _renderable if exposed, but render() is safer.
            self.assertIn("Result:", str(lbl.render()))

if __name__ == "__main__":
    unittest.main()
