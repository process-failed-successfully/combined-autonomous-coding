import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path

# Add shared to path
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402

from shared.tui_dns import DnsLabTab  # noqa: E402
from textual.widgets import Input, Select, DataTable, RichLog  # noqa: E402


class TestDnsLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = DnsLabTab()
        # Mock internal managers
        self.tab.dns_manager = MagicMock()
        self.tab.whois_manager = MagicMock()

        # Mock query_one to return mocks for widgets
        self.tab.query_one = MagicMock()
        self.mock_input = MagicMock(spec=Input)
        self.mock_select = MagicMock(spec=Select)
        self.mock_log = MagicMock(spec=RichLog)
        self.mock_table = MagicMock(spec=DataTable)
        self.tab.notify = MagicMock()

    async def test_run_lookup_success(self):
        # Setup widget values
        self.mock_input.value = "example.com"
        self.mock_select.value = "A"

        def query_side_effect(selector, type=None):
            if "domain" in selector:
                return self.mock_input
            if "type" in selector:
                return self.mock_select
            if "server" in selector:
                return self.mock_select
            if "log" in selector:
                return self.mock_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Response
        self.tab.dns_manager.lookup = MagicMock(return_value={"records": ["1.2.3.4"]})

        # Run
        await self.tab.run_lookup()

        # Verify
        self.tab.dns_manager.lookup.assert_called_with("example.com", "A", None)
        self.mock_log.write.assert_any_call("[bold green]Records found:[/bold green]")
        self.mock_log.write.assert_any_call("  1.2.3.4")

    async def test_run_lookup_error(self):
        self.mock_input.value = "error.com"
        self.mock_select.value = "A"

        def query_side_effect(selector, type=None):
            if "domain" in selector:
                return self.mock_input
            if "type" in selector:
                return self.mock_select
            if "server" in selector:
                return self.mock_select
            if "log" in selector:
                return self.mock_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.dns_manager.lookup = MagicMock(return_value={"error": "NXDOMAIN"})

        await self.tab.run_lookup()

        self.mock_log.write.assert_called_with("[bold red]Error: NXDOMAIN[/bold red]")
        self.tab.notify.assert_called_with("Lookup failed.", severity="error")

    async def test_run_propagation(self):
        self.mock_input.value = "prop.com"
        self.mock_select.value = "A"

        def query_side_effect(selector, type=None):
            if "domain" in selector:
                return self.mock_input
            if "type" in selector:
                return self.mock_select
            if "table" in selector:
                return self.mock_table
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # Mock results
        results = {
            "Google": ["1.1.1.1"],
            "Cloudflare": {"error": "Timeout"}
        }
        self.tab.dns_manager.check_propagation = MagicMock(return_value=results)

        await self.tab.run_propagation()

        self.mock_table.clear.assert_called()
        # Verify table rows added
        # Google row
        self.mock_table.add_row.assert_any_call("Google", "8.8.8.8", "1.1.1.1", "[green]OK[/green]")
        # Cloudflare row
        self.mock_table.add_row.assert_any_call("Cloudflare", "1.1.1.1", "Timeout", "[red]Error[/red]")

    async def test_run_whois_lookup(self):
        self.mock_input.value = "whois.com"

        def query_side_effect(selector, type=None):
            if "domain" in selector:
                return self.mock_input
            if "log" in selector:
                return self.mock_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.whois_manager.lookup = MagicMock(return_value="WHOIS DATA")

        await self.tab.run_whois(check_availability=False)

        self.tab.whois_manager.lookup.assert_called_with("whois.com")
        self.mock_log.write.assert_any_call("WHOIS DATA")

    async def test_run_whois_availability(self):
        self.mock_input.value = "free.com"

        def query_side_effect(selector, type=None):
            if "domain" in selector:
                return self.mock_input
            if "log" in selector:
                return self.mock_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        self.tab.whois_manager.check_availability = MagicMock(return_value={
            "available": True,
            "output": "No match found"
        })

        await self.tab.run_whois(check_availability=True)

        self.tab.whois_manager.check_availability.assert_called_with("free.com")
        self.mock_log.write.assert_any_call("[bold green]AVAILABLE[/bold green]: free.com")


if __name__ == "__main__":
    unittest.main()
