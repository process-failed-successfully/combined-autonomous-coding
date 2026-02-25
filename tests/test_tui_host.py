import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, Input, DataTable
from shared.tui_host import HostLabTab

class TestHostLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.tui_host.HostLabManager")
    def test_load_entries(self, MockManager):
        """Test that load_entries populates the table."""
        mock_manager = MockManager.return_value
        mock_manager.list_entries.return_value = [
            {'type': 'entry', 'enabled': True, 'ip': '1.2.3.4', 'hosts': ['example.com'], 'comment': 'Test', 'line_num': 1}
        ]

        tab = HostLabTab(self.project_dir)

        # Mock widgets
        mock_table = MagicMock(spec=DataTable)
        tab.query_one = MagicMock(return_value=mock_table)

        tab.load_entries()

        mock_manager.list_entries.assert_called_once()
        mock_table.clear.assert_called_once()
        # Verify add_row called with correct data
        args, kwargs = mock_table.add_row.call_args
        self.assertIn("[green]Active[/green]", args[0])
        self.assertEqual(args[1], "1.2.3.4")
        self.assertEqual(args[2], "example.com")
        self.assertEqual(kwargs['key'], "1")

    @patch("shared.tui_host.HostLabManager")
    async def test_add_entry(self, MockManager):
        """Test adding a new entry."""
        mock_manager = MockManager.return_value
        mock_manager.add_entry.return_value = True

        tab = HostLabTab(self.project_dir)

        # Mock inputs
        mock_ip = MagicMock(spec=Input)
        mock_ip.value = "10.0.0.1"
        mock_host = MagicMock(spec=Input)
        mock_host.value = "test.local"
        mock_comment = MagicMock(spec=Input)
        mock_comment.value = ""

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#input-host-ip": mock_ip,
            "#input-host-name": mock_host,
            "#input-host-comment": mock_comment,
            "#host-table": MagicMock(spec=DataTable)
        }.get(selector))

        # Mock notify
        tab.notify = MagicMock()
        # Mock load_entries to avoid actual call issues
        tab.load_entries = MagicMock()

        # Trigger button press
        event = MagicMock()
        event.button.id = "btn-host-add"

        await tab.on_button_pressed(event)

        mock_manager.add_entry.assert_called_with("10.0.0.1", "test.local", "")
        tab.notify.assert_called_with("Added test.local")

    @patch("shared.tui_host.HostLabManager")
    async def test_toggle_entry(self, MockManager):
        """Test toggling an entry."""
        mock_manager = MockManager.return_value
        mock_manager.toggle_entry.return_value = True

        tab = HostLabTab(self.project_dir)
        tab.selected_host = "test.local"
        tab.notify = MagicMock()
        tab.load_entries = MagicMock()

        event = MagicMock()
        event.button.id = "btn-host-toggle"

        await tab.on_button_pressed(event)

        mock_manager.toggle_entry.assert_called_with("test.local")
        tab.notify.assert_called_with("Toggled test.local")

if __name__ == "__main__":
    unittest.main()
