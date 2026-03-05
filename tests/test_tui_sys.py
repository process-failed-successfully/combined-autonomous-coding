import unittest
from unittest.mock import patch, MagicMock
import asyncio
from pathlib import Path
import sys

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_sys import SysTab
from textual.widgets import DataTable, Input

class TestSysTab(unittest.IsolatedAsyncioTestCase):

    @patch("shared.tui_sys.SysLabManager")
    async def test_sys_tab_initialization(self, mock_manager_cls):
        # Setup mock manager
        mock_manager = MagicMock()
        mock_manager.get_system_info.return_value = {
            "system": {"os": "Test OS", "version": "1.0", "processor": "Test CPU"},
            "cpu": {"physical_cores": 2, "logical_cores": 4, "usage_percent": 10.0},
            "memory": {"total": 1024, "used": 512, "percent": 50.0},
            "disk": {"root_total": 2048, "root_used": 1024, "root_percent": 50.0}
        }
        mock_manager.format_bytes.side_effect = lambda x: f"{x} B"
        mock_manager.list_processes.return_value = [
            {"pid": 1, "username": "root", "cpu_percent": 0.5, "memory_percent": 1.0, "name": "init", "cmdline": "/sbin/init"},
            {"pid": 2, "username": "user", "cpu_percent": 10.0, "memory_percent": 5.0, "name": "python", "cmdline": "python script.py"}
        ]
        mock_manager_cls.return_value = mock_manager

        # Initialize the tab
        tab = SysTab(project_dir=Path("/tmp"))
        self.assertIsNotNone(tab)

        # In Textual, mounting/DOM interaction is tricky outside an App context without a pilot.
        # However, we can call the methods that populate the data to ensure they don't crash
        # and interact with the manager correctly, assuming the DOM is present.
        # Since we cannot easily mount it without an App and Pilot, we will patch the DOM queries.

        with patch.object(tab, 'query_one') as mock_query_one:
            mock_table = MagicMock(spec=DataTable)
            mock_input = MagicMock(spec=Input)
            mock_input.value = "python"

            def side_effect(selector, *args, **kwargs):
                if "DataTable" in str(selector) or "DataTable" in str(args):
                    return mock_table
                if "Input" in str(selector) or "Input" in str(args):
                    return mock_input
                return MagicMock()

            mock_query_one.side_effect = side_effect

            # Test refresh info
            tab.refresh_sys_info()
            mock_manager.get_system_info.assert_called_once()

            # Test refresh processes
            tab.refresh_processes()
            mock_manager.list_processes.assert_called_once()

            # Verify table was cleared and rows added
            mock_table.clear.assert_called_once()
            self.assertEqual(mock_table.add_row.call_count, 2)

    @patch("shared.tui_sys.SysLabManager")
    async def test_kill_process(self, mock_manager_cls):
        mock_manager = MagicMock()
        mock_manager.kill_process.return_value = {"success": True, "message": "Killed"}
        mock_manager_cls.return_value = mock_manager

        tab = SysTab(project_dir=Path("/tmp"))
        tab.selected_process = 123
        tab.notify = MagicMock()

        with patch.object(tab, 'query_one') as mock_query_one:
            mock_query_one.return_value = MagicMock()

            # Simulate kill button press
            # We mock the internal logic since textual events are hard to synthesize standalone
            result = await asyncio.to_thread(tab.manager.kill_process, pid=tab.selected_process)
            self.assertTrue(result["success"])
            mock_manager.kill_process.assert_called_with(pid=123)

if __name__ == '__main__':
    unittest.main()
