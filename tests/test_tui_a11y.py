import unittest
from unittest.mock import patch
from pathlib import Path


# Provide a fake app to avoid Textual instantiation errors during test without pilot
class DummyApp:
    def notify(self, message, severity="info", title=""):
        self.last_notification = message


class TestA11yTab(unittest.IsolatedAsyncioTestCase):
    async def test_a11y_tab_rendering_and_scan(self):
        """Test A11yTab UI elements and scan logic interaction."""
        from shared.tui_a11y import A11yTab
        from textual.widgets import Input, Button, DataTable

        tab = A11yTab()

        # Patch app
        tab._app = DummyApp()

        # We need to test the compose and actions using a pilot
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield tab

        app = TestApp()
        async with app.run_test() as pilot:
            # Check inputs are present
            dir_input = app.query_one("#a11y_dir_input", Input)
            self.assertIsNotNone(dir_input)

            pattern_input = app.query_one("#a11y_pattern_input", Input)
            self.assertIsNotNone(pattern_input)

            # Check button is present
            scan_btn = app.query_one("#a11y_scan_btn", Button)
            self.assertIsNotNone(scan_btn)

            # Check datatable
            table = app.query_one("#a11y_table", DataTable)
            self.assertIsNotNone(table)

            # Create a fake file with an a11y issue
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                test_dir = Path(d)
                test_file = test_dir / "index.html"
                test_file.write_text("<html><body><img src='test.jpg'></body></html>")

                # Update UI
                dir_input.value = str(test_dir)

                # Mock notify to prevent UI app access errors
                with patch.object(app, 'notify') as mock_notify:
                    # trigger scan
                    app.query_one("#a11y_scan_btn", Button).press()
                    await pilot.pause()

                    # Ensure table was populated (img missing alt, html missing lang)
                    self.assertTrue(len(table.rows) > 0)
                    mock_notify.assert_called()
