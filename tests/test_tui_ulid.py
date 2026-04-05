import unittest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

from textual.app import App
from textual.widgets import TabbedContent
from shared.tui_ulid import UlidLabTab

class DummyApp(App):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self):
        yield UlidLabTab()

class TestUlidLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = DummyApp()
        self.tab = None

    async def test_generate(self):
        async with self.app.run_test() as pilot:
            self.tab = pilot.app.query_one(UlidLabTab)
            self.tab.notify = MagicMock()

            # Click generate
            app.query_one("#btn-ulid-generate").press()
        await pilot.pause()
            await pilot.pause()

            log = pilot.app.query_one("#log-ulid-generate")
            lines = list(log.lines)
            self.assertTrue(len(lines) > 0)
            self.tab.notify.assert_called_with("Generated 1 ULIDs.")

    async def test_inspect_empty(self):
        async with self.app.run_test() as pilot:
            self.tab = pilot.app.query_one(UlidLabTab)
            self.tab.notify = MagicMock()

            tabs = pilot.app.query_one(TabbedContent)
            tabs.active = "tab-2" # inspect is usually second
            await pilot.pause()

            # Switch tab if needed, but we can just query the button
            # app.query_one("#btn-ulid-inspect").press()
        await pilot.pause() might fail due to bounds if not visible, we can just call it
            self.tab.on_inspect()

            self.tab.notify.assert_called_with("Please enter a ULID.", severity="warning")

    async def test_validate_invalid(self):
        async with self.app.run_test() as pilot:
            self.tab = pilot.app.query_one(UlidLabTab)

            input_widget = pilot.app.query_one("#input-ulid-validate")
            input_widget.value = "invalid_string"

            self.tab.on_validate()
            await pilot.pause()

            lbl = pilot.app.query_one("#lbl-ulid-validate-result")
            self.assertIn("Invalid ULID", str(lbl.render()))

if __name__ == '__main__':
    unittest.main()
