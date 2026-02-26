import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import DirectoryTree, DataTable, Input, RichLog, Button
from textual import events

# Mock the shared.pcap_lab module
import sys
mock_pcap_lab = MagicMock()
sys.modules["shared.pcap_lab"] = mock_pcap_lab

# Now import the TUI component
from shared.tui_pcap import PcapLabTab, PcapDirectoryTree

class PcapLabTestApp(App):
    """A minimal app to test PcapLabTab."""
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield PcapLabTab(self.project_dir)

class TestPcapLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.app = PcapLabTestApp(self.project_dir)

    async def test_initial_state(self):
        """Test that the tab initializes with correct widgets."""
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(PcapLabTab)
            # Use specific types or IDs that exist
            self.assertIsNotNone(tab.query_one("#pcap-tree", PcapDirectoryTree))
            self.assertIsNotNone(tab.query_one("#pcap-table", DataTable))
            self.assertIsNotNone(tab.query_one("#pcap-summary-log", RichLog))
            self.assertIsNotNone(tab.query_one("#pcap-filter-input", Input))
            self.assertIsNotNone(tab.query_one("#btn-pcap-load", Button))

    async def test_filter_update(self):
        """Test that typing in the filter input triggers logic."""
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(PcapLabTab)

            input_widget = tab.query_one("#pcap-filter-input", Input)

            # Force focus
            input_widget.focus()

            # Simulate user typing
            await pilot.press("t", "c", "p")

            # Wait for events to process
            await pilot.pause()

            # Check value
            self.assertEqual(input_widget.value, "tcp")

    async def test_load_button_disabled_initially(self):
        """Test that load button is disabled until file selection."""
        async with self.app.run_test() as pilot:
            tab = self.app.query_one(PcapLabTab)
            btn = tab.query_one("#btn-pcap-load", Button)
            self.assertTrue(btn.disabled)

if __name__ == "__main__":
    unittest.main()
