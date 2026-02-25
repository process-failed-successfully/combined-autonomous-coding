import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_systemd import SystemdLabTab


class MockApp(App):
    def compose(self) -> ComposeResult:
        yield SystemdLabTab(Path("."))


class TestSystemdLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_manager_patcher = patch('shared.tui_systemd.SystemdManager')
        self.mock_manager_cls = self.mock_manager_patcher.start()
        self.mock_manager = self.mock_manager_cls.return_value

        # Setup default mock returns
        self.mock_manager.list_units.return_value = [
            {"unit": "test.service", "load": "loaded", "active": "active", "sub": "running", "description": "Test Service"}
        ]
        self.mock_manager.get_status.return_value = "Active: active (running)"
        self.mock_manager.control_service.return_value = (True, "Success")
        self.mock_manager.get_logs.return_value = "Log line 1\nLog line 2"
        self.mock_manager.generate_unit_file.return_value = "[Unit]\nDescription=Test"

    async def asyncTearDown(self):
        self.mock_manager_patcher.stop()

    async def test_initialization(self):
        app = MockApp()
        async with app.run_test() as pilot:
            # Check if table is populated
            table = pilot.app.query_one("#systemd-table")
            self.assertEqual(table.row_count, 1)

            # Check row content (Textual DataTable returns Row object or similar, keys are tricky)
            # We assume it loaded because row_count is 1

            # Check buttons are disabled initially
            btn = pilot.app.query_one("#btn-systemd-start")
            self.assertTrue(btn.disabled)

    async def test_selection_and_control(self):
        app = MockApp()
        async with app.run_test() as pilot:
            # Select the row
            table = pilot.app.query_one("#systemd-table")
            # In Textual, we can simulate click on a cell/row if we know coordinates or ID
            # Or we can programmatically trigger the event if difficult to simulate click on dynamic table
            # Let's try to programmatically select

            # Textual 0.38+ DataTable has methods to move cursor or select
            # We rely on key being set to unit name
            table.move_cursor(row=0)
            # Triggering selection manually because move_cursor might not trigger on_row_selected automatically depending on config?
            # But wait, cursor_type="row".
            # Simulate pressing 'enter' on the table to select? Or click.

            await pilot.click("#systemd-table")  # Might click header or empty space

            # Easier: direct method call to simulate logic if UI interaction is flaky in mock env
            # But we want to test wiring.
            # Let's manually trigger the handler if possible, or assume selecting row 0 works.

            # Force selection logic
            tab = pilot.app.query_one(SystemdLabTab)
            tab.on_row_selected(MagicMock(row_key=MagicMock(value="test.service")))

            # Check button enabled
            btn = pilot.app.query_one("#btn-systemd-start")
            self.assertFalse(btn.disabled)

            # Click Start
            await pilot.click("#btn-systemd-start")

            # Verify manager call
            self.mock_manager.control_service.assert_called_with("test.service", "start")

    async def test_generate(self):
        app = MockApp()
        async with app.run_test() as pilot:
            # Switch tab? (TabbedContent)
            # Programmatically switch
            tabs = pilot.app.query_one("TabbedContent")
            tabs.active = "tab-2"  # Textual auto-ids are usually tab-1, tab-2 if not specified.
            # But we generated panes. Let's find by label?
            # Actually we can just input fields and click generate, assuming they are in DOM.

            await pilot.click("#gen-sys-name")
            await pilot.press("t", "e", "s", "t")

            await pilot.click("#gen-sys-cmd")
            await pilot.press("e", "c", "h", "o")

            await pilot.click("#btn-systemd-generate")

            # Verify manager call
            # Note: inputs might not fully update with 'press' if not focused correctly or timing.
            # We can set value directly.
            pilot.app.query_one("#gen-sys-name").value = "myservice"
            pilot.app.query_one("#gen-sys-cmd").value = "/bin/true"

            await pilot.click("#btn-systemd-generate")

            self.mock_manager.generate_unit_file.assert_called()
            args, kwargs = self.mock_manager.generate_unit_file.call_args
            self.assertEqual(kwargs['name'], "myservice")
            self.assertEqual(kwargs['command'], "/bin/true")


if __name__ == "__main__":
    unittest.main()
