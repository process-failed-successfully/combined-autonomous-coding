import unittest
from unittest.mock import MagicMock, patch
from shared.tui_cidr import CidrLabTab
from textual.app import App
from textual.widgets import TabbedContent, RichLog

class DummyApp(App):
    def compose(self):
        yield CidrLabTab()

    async def on_mount(self):
        self.notify = MagicMock()

class TestCidrLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_info_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "cidr-tab-info"
            await pilot.pause()

            app.query_one("#cidr-info-input").value = "192.168.1.0/24"

            mock_info_res = {
                "cidr": "192.168.1.0/24",
                "netmask": "255.255.255.0",
                "num_addresses": 256
            }

            with patch('shared.tui_cidr.CidrLabManager.get_info', return_value=mock_info_res) as mock_info:
                await pilot.click("#btn-cidr-info")
                mock_info.assert_called_once_with("192.168.1.0/24")
                log = app.query_one("#cidr-info-log", RichLog)
                self.assertTrue(any("255.255.255.0" in line.text for line in log.lines))

    async def test_contains_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "cidr-tab-contains"
            await pilot.pause()

            app.query_one("#cidr-contains-container").value = "10.0.0.0/8"
            app.query_one("#cidr-contains-target").value = "10.1.2.3"

            mock_contains_res = {
                "container": "10.0.0.0/8",
                "target": "10.1.2.3",
                "contains": True,
                "type": "address"
            }

            with patch('shared.tui_cidr.CidrLabManager.contains', return_value=mock_contains_res) as mock_contains:
                await pilot.click("#btn-cidr-contains")
                mock_contains.assert_called_once_with("10.0.0.0/8", "10.1.2.3")
                log = app.query_one("#cidr-contains-log", RichLog)
                self.assertTrue(any("contains address" in line.text for line in log.lines))

    async def test_overlaps_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "cidr-tab-overlaps"
            await pilot.pause()

            app.query_one("#cidr-overlaps-1").value = "192.168.1.0/24"
            app.query_one("#cidr-overlaps-2").value = "192.168.0.0/16"

            mock_overlaps_res = {
                "cidr1": "192.168.1.0/24",
                "cidr2": "192.168.0.0/16",
                "overlaps": True
            }

            with patch('shared.tui_cidr.CidrLabManager.overlaps', return_value=mock_overlaps_res) as mock_overlaps:
                await pilot.click("#btn-cidr-overlaps")
                mock_overlaps.assert_called_once_with("192.168.1.0/24", "192.168.0.0/16")
                log = app.query_one("#cidr-overlaps-log", RichLog)
                self.assertTrue(any("OVERLAP" in line.text for line in log.lines))

    async def test_subnet_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "cidr-tab-subnet"
            await pilot.pause()

            app.query_one("#cidr-subnet-base").value = "192.168.1.0/24"
            app.query_one("#cidr-subnet-prefix").value = "25"

            mock_subnet_res = {
                "cidr": "192.168.1.0/24",
                "new_prefix": 25,
                "count": 2,
                "subnets": ["192.168.1.0/25", "192.168.1.128/25"]
            }

            with patch('shared.tui_cidr.CidrLabManager.subnet', return_value=mock_subnet_res) as mock_subnet:
                await pilot.click("#btn-cidr-subnet")
                mock_subnet.assert_called_once_with("192.168.1.0/24", 25)
                log = app.query_one("#cidr-subnet-log", RichLog)
                self.assertTrue(any("192.168.1.128/25" in line.text for line in log.lines))

if __name__ == '__main__':
    unittest.main()
