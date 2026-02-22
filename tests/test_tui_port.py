import unittest
from unittest.mock import patch
from textual.app import App, ComposeResult
from shared.tui_port import PortLabTab
from textual.widgets import DataTable, Button, Input


class PortLabApp(App):
    def compose(self) -> ComposeResult:
        yield PortLabTab()


class TestPortLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_port_lab_tab(self):
        # Mock PortManager
        with patch('shared.tui_port.PortManager') as MockPortManager:
            # Setup mock return values
            MockPortManager.list_listening_ports.return_value = [
                {"port": 8080, "pid": 1234, "name": "python", "username": "user"},
                {"port": 3000, "pid": 5678, "name": "node", "username": "user"}
            ]
            MockPortManager.kill_process_on_port.return_value = True

            app = PortLabApp()
            async with app.run_test() as pilot:
                # Check if table is populated
                table = app.query_one(DataTable)
                self.assertEqual(table.row_count, 2)

                # Test Filter
                inp = app.query_one("#input-port-filter", Input)
                inp.value = "python"
                await pilot.pause()

                # Should filter to 1 row
                self.assertEqual(table.row_count, 1)

                # Test Kill Button enable
                kill_btn = app.query_one("#btn-kill-port", Button)
                self.assertTrue(kill_btn.disabled)

                # Select the row.
                # Move cursor to first row (which is visible) and select it.
                table.move_cursor(row=0)
                # In Textual, move_cursor doesn't trigger selection event on its own unless select_on_cursor is True
                # But action_select_cursor() does.
                table.action_select_cursor()
                await pilot.pause()

                self.assertFalse(kill_btn.disabled, "Kill button should be enabled after selection")

                # Click Kill
                await pilot.click("#btn-kill-port")
                await pilot.pause()

                # Verify kill called
                MockPortManager.kill_process_on_port.assert_called_with(8080)

                # Verify reload called
                self.assertGreaterEqual(MockPortManager.list_listening_ports.call_count, 2)


if __name__ == "__main__":
    unittest.main()
