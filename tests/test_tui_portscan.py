import unittest
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from textual.app import App
import sys
import asyncio

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.tui_portscan import PortScanTab
from shared.portscan_lab import PortScanManager

class DummyApp(App):
    """Dummy app for testing PortScanTab."""
    def compose(self):
        yield PortScanTab()

class TestPortScanTab(unittest.IsolatedAsyncioTestCase):

    async def test_initial_state(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PortScanTab)

            # Check inputs
            self.assertEqual(tab.query_one("#portscan-host").value, "127.0.0.1")
            self.assertEqual(tab.query_one("#portscan-ports").value, "1-1024")

            # Check buttons
            self.assertFalse(tab.query_one("#btn-portscan").disabled)
            self.assertTrue(tab.query_one("#btn-portscan-cancel").disabled)

    @patch('shared.tui_portscan.PortScanManager.scan_ports')
    async def test_start_scan_valid(self, mock_scan_ports):
        # Setup mock to return a completed scan
        async def mock_scan(*args, **kwargs):
            return [{"port": "80", "service": "HTTP"}]
        mock_scan_ports.side_effect = mock_scan

        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PortScanTab)

            # Click scan
            btn = tab.query_one("#btn-portscan")
            btn.press()
            await asyncio.sleep(0.1) # Yield to event loop

            # Wait for task
            if tab.scan_task:
                await tab.scan_task

            # Check if UI updated
            status = tab.query_one("#portscan-status")
            self.assertIn("complete", str(status.render()))

    @patch('shared.tui_portscan.PortScanManager.scan_ports')
    async def test_cancel_scan(self, mock_scan_ports):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PortScanTab)

            # Set to scanning state manually for simplicity
            tab.is_scanning = True

            # Click cancel
            btn = tab.query_one("#btn-portscan-cancel")
            btn.press()

            await asyncio.sleep(0.1) # yield

            # Check state
            self.assertFalse(tab.is_scanning)
            status = tab.query_one("#portscan-status")
            self.assertIn("cancelled", str(status.render()))

    async def test_invalid_ports(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PortScanTab)

            # Set invalid ports
            tab.query_one("#portscan-ports").value = "invalid"

            # Click scan
            btn = tab.query_one("#btn-portscan")
            btn.press()

            # Should not be scanning
            self.assertFalse(tab.is_scanning)

    async def test_invalid_options(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tab = app.query_one(PortScanTab)

            # Set invalid timeout
            tab.query_one("#portscan-timeout").value = "invalid"

            # Click scan
            btn = tab.query_one("#btn-portscan")
            btn.press()

            # Should not be scanning
            self.assertFalse(tab.is_scanning)

if __name__ == '__main__':
    unittest.main()
