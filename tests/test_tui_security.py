import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Button, RichLog
from shared.tui_security import SecurityTab

class SecurityTestApp(App):
    def __init__(self, project_dir):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield SecurityTab(self.project_dir)

class TestSecurityTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = SecurityTestApp(self.project_dir)

    @patch("shared.tui_security.SecurityAuditor")
    async def test_scan_population(self, MockAuditor):
        # Setup Mock
        mock_instance = MockAuditor.return_value
        mock_instance.run_all.return_value = [
            {
                "type": "secret",
                "severity": "HIGH",
                "description": "Found a secret key",
                "file": "config.py",
                "line": 10,
                "snippet": "API_KEY = '12345'"
            },
            {
                "type": "sast",
                "severity": "MEDIUM",
                "description": "Use of eval",
                "file": "utils.py",
                "line": 5,
                "snippet": "eval(user_input)"
            }
        ]

        async with self.app.run_test() as pilot:
            # Verify initial state
            tab = self.app.query_one(SecurityTab)
            table = tab.query_one("#sec-findings-table", DataTable)
            self.assertEqual(table.row_count, 0)

            # Click Scan Button
            app.query_one("#btn-sec-scan-all").press()
        await pilot.pause()

            # Wait for async operation (Textual tests usually wait for events)
            # Since run_scan calls auditor in a thread, we might need to wait a bit
            # textual's pilot.pause() might help if there are pending tasks
            await pilot.pause()

            # Verify table populated
            self.assertEqual(table.row_count, 2)

            # Verify content of first row (High severity should be first)
            row = table.get_row_at(0)
            self.assertIn("HIGH", str(row[0])) # Textual renders rich text, so str() might contain markup
            self.assertEqual(row[1], "secret")
            self.assertEqual(row[2], "config.py")

    @patch("shared.tui_security.SecurityAuditor")
    async def test_ignore_file(self, MockAuditor):
        # Setup Mock
        mock_instance = MockAuditor.return_value
        mock_instance.run_all.return_value = [
            {
                "type": "secret",
                "severity": "HIGH",
                "description": "Found a secret key",
                "file": "config.py",
                "line": 10,
                "snippet": "API_KEY = '12345'"
            }
        ]

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(SecurityTab)

            # Populate
            app.query_one("#btn-sec-scan-all").press()
        await pilot.pause()
            await pilot.pause()

            # Select row
            table = tab.query_one("#sec-findings-table", DataTable)
            table.cursor_coordinate = (0, 0)
            # Trigger selection event manually or via pilot
            # pilot.click on a cell might works if supported, but programmatic selection is safer for unit test
            # pilot.press("enter") on the table works if it has focus
            table.focus()
            await pilot.press("enter")
            await pilot.pause()

            # Verify details shown
            log = tab.query_one("#sec-details-log", RichLog)
            # RichLog content is hard to read back directly in some versions, but we can check internal state
            self.assertIsNotNone(tab.selected_finding)
            self.assertEqual(tab.selected_finding["file"], "config.py")

            # Click Ignore
            app.query_one("#btn-sec-ignore-file").press()
        await pilot.pause()

            # Verify auditor call
            mock_instance.add_ignore_pattern.assert_called_with("config.py")

if __name__ == "__main__":
    unittest.main()
