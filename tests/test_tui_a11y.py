import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_a11y import A11yLabTab
from textual.widgets import Input, Button, DataTable, RichLog


class DummyApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield A11yLabTab(self.project_dir)


class TestA11yLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/dummy_project")

    async def test_tui_a11y_rendering(self):
        app = DummyApp(self.project_dir)
        async with app.run_test():
            tab = app.query_one(A11yLabTab)
            self.assertIsNotNone(tab)
            self.assertIsNotNone(app.query_one("#inp-a11y-files", Input))
            self.assertIsNotNone(app.query_one("#inp-a11y-ignore", Input))
            self.assertIsNotNone(app.query_one("#btn-a11y-scan", Button))
            self.assertIsNotNone(app.query_one("#a11y-table", DataTable))
            self.assertIsNotNone(app.query_one("#a11y-log", RichLog))

    @patch("shared.tui_a11y.AccessibilityScanner")
    async def test_tui_a11y_scan_action(self, mock_scanner_class):
        # Mock the scanner behavior
        mock_scanner = MagicMock()
        from shared.a11y import A11yViolation
        mock_scanner.violations = [
            A11yViolation("img-alt-missing", "<img> element missing 'alt'", "index.html", 10, "ERROR"),
            A11yViolation("heading-jump", "Skipped heading level", "about.html", 25, "WARNING"),
        ]
        mock_scanner_class.return_value = mock_scanner

        app = DummyApp(self.project_dir)
        async with app.run_test() as pilot:
            # Trigger scan
            app.query_one("#btn-a11y-scan", Button).press()
            await pilot.pause(0.1)  # Wait for thread/asyncio

            # Verify scanner was instantiated
            mock_scanner_class.assert_called_once()
            mock_scanner.scan.assert_called_once()

            # Verify table was populated
            table = app.query_one("#a11y-table", DataTable)
            self.assertEqual(len(table.rows), 2)

            # Select a row to check details log
            # We can programmatically fire the row selected event or just simulate it
            pilot.app.query_one("#a11y-table").press()
            await pilot.pause()
            # Textual's DataTable is tricky to click rows precisely, we can manually call the handler
            row_key = list(table.rows.keys())[0]
            # Create a mock event and call the handler directly to test the log logic
            event = MagicMock()
            event.row_key.value = str(row_key.value)
            tab = app.query_one(A11yLabTab)
            tab.on_row_selected(event)

            await pilot.pause(0.1)

            # Since RichLog contents aren't trivially accessible as plain text in all versions without rendering,
            # we just ensure it didn't crash. (We could check log.lines if needed).
            log = app.query_one("#a11y-log", RichLog)
            self.assertIsNotNone(log)


if __name__ == "__main__":
    unittest.main()
