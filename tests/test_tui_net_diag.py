import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.widgets import Input, RichLog, DataTable, Select, Label
from shared.tui_net_diag import NetDiagTab

class TestNetDiagTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        # We patch NetLabManager class to avoid real init if it does anything heavy (it doesn't, but good practice)
        with patch("shared.tui_net_diag.NetLabManager") as MockManager:
            self.tab = NetDiagTab(self.project_dir)
            self.mock_manager = MockManager.return_value
            self.tab.manager = self.mock_manager # Ensure we control the instance

        # Mock Textual UI methods
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def test_run_ping(self):
        # Mock Inputs
        host_input = MagicMock(spec=Input)
        host_input.value = "example.com"
        count_input = MagicMock(spec=Input)
        count_input.value = "2"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#ping-host": return host_input
            if selector == "#ping-count": return count_input
            if selector == "#ping-log": return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.ping.return_value = True

        # Run
        await self.tab.run_ping()

        # Verify
        self.mock_manager.ping.assert_called_with("example.com", 2)
        log.write.assert_called() # Should write success message
        self.tab.notify.assert_called_with("Ping successful.")

    async def test_run_scan(self):
        # Mock Inputs
        host_input = MagicMock(spec=Input)
        host_input.value = "localhost"
        ports_input = MagicMock(spec=Input)
        ports_input.value = "80,443"
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#scan-host": return host_input
            if selector == "#scan-ports": return ports_input
            if selector == "#scan-table": return table
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.scan_ports.return_value = {80: "Open", 443: "Closed"}

        # Run
        await self.tab.run_scan()

        # Verify
        self.mock_manager.scan_ports.assert_called()
        # Check args passed to scan_ports
        args, _ = self.mock_manager.scan_ports.call_args
        self.assertEqual(args[0], "localhost")
        self.assertEqual(sorted(args[1]), [80, 443])

        # Verify table update
        table.clear.assert_called()
        self.assertEqual(table.add_row.call_count, 2)

    async def test_run_dns(self):
        # Mock Inputs
        domain_input = MagicMock(spec=Input)
        domain_input.value = "example.com"
        type_select = MagicMock(spec=Select)
        type_select.value = "A"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#dns-domain": return domain_input
            if selector == "#dns-type": return type_select
            if selector == "#dns-log": return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.dns_lookup.return_value = {"A": ["1.2.3.4"]}

        # Run
        await self.tab.run_dns()

        # Verify
        self.mock_manager.dns_lookup.assert_called_with("example.com", "A")
        log.write.assert_called()

    async def test_run_http(self):
        # Mock Inputs
        url_input = MagicMock(spec=Input)
        url_input.value = "http://example.com"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#http-url": return url_input
            if selector == "#http-log": return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.http_head.return_value = {"status_code": 200, "headers": {"Server": "Test"}}

        # Run
        await self.tab.run_http()

        # Verify
        self.mock_manager.http_head.assert_called_with("http://example.com")
        log.write.assert_called()

    async def test_run_ip(self):
        # Mock Labels
        lbl_local = MagicMock(spec=Label)
        lbl_public = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#lbl-local-ip": return lbl_local
            if selector == "#lbl-public-ip": return lbl_public
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.get_ip_info.return_value = {"local_ip": "192.168.1.5", "public_ip": "8.8.8.8"}

        # Run
        await self.tab.run_ip()

        # Verify
        self.mock_manager.get_ip_info.assert_called()
        lbl_local.update.assert_called()
        lbl_public.update.assert_called()

if __name__ == "__main__":
    unittest.main()
