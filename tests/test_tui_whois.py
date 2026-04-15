import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, Button, Label, RichLog
import pytest

from shared.tui_whois import WhoisLabTab

class TestWhoisLabTab(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_whois.WhoisLabManager")
        self.MockManager = self.patcher.start()

        self.tab = WhoisLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_action_lookup_success(self):
        domain_input = MagicMock(spec=Input)
        domain_input.value = "example.com"
        server_input = MagicMock(spec=Input)
        server_input.value = ""
        status_lbl = MagicMock(spec=Label)

        self.tab.query_one.side_effect = lambda selector, _: {
            "#whois-domain": domain_input,
            "#whois-server": server_input,
            "#whois-status": status_lbl,
            "#btn-whois-lookup": MagicMock(),
            "#btn-whois-check": MagicMock()
        }[selector]

        self.tab.output_log = MagicMock(spec=RichLog)
        self.mock_manager.lookup.return_value = "Mock WHOIS info for example.com"

        await self.tab.action_lookup()

        self.mock_manager.lookup.assert_called_once_with("example.com", None)
        self.tab.output_log.write.assert_called_once_with("Mock WHOIS info for example.com")
        status_lbl.update.assert_called_with("Lookup complete for example.com.")
        self.assertFalse(self.tab.is_querying)

    async def test_action_lookup_no_domain(self):
        domain_input = MagicMock(spec=Input)
        domain_input.value = ""
        server_input = MagicMock(spec=Input)
        server_input.value = ""

        self.tab.query_one.side_effect = lambda selector, _: {
            "#whois-domain": domain_input,
            "#whois-server": server_input
        }[selector]

        await self.tab.action_lookup()

        self.tab.notify.assert_called_once_with("Please enter a domain.", title="Error", severity="error")
        self.mock_manager.lookup.assert_not_called()

    async def test_action_check_available(self):
        domain_input = MagicMock(spec=Input)
        domain_input.value = "example.xyz"
        status_lbl = MagicMock(spec=Label)

        self.tab.query_one.side_effect = lambda selector, _: {
            "#whois-domain": domain_input,
            "#whois-status": status_lbl,
            "#btn-whois-lookup": MagicMock(),
            "#btn-whois-check": MagicMock(),
            "#whois-server": MagicMock()
        }[selector]

        self.tab.output_log = MagicMock(spec=RichLog)
        self.mock_manager.check_availability.return_value = {
            "available": True,
            "output": "Domain is free"
        }

        await self.tab.action_check()

        self.mock_manager.check_availability.assert_called_once_with("example.xyz")
        status_lbl.update.assert_called_with("✅ Domain 'example.xyz' appears to be AVAILABLE.")
        self.tab.notify.assert_called_with("Domain 'example.xyz' appears to be AVAILABLE.", title="Whois Check", severity="information")
        self.tab.output_log.write.assert_any_call("Domain is free")

    async def test_action_check_taken(self):
        domain_input = MagicMock(spec=Input)
        domain_input.value = "google.com"
        status_lbl = MagicMock(spec=Label)

        self.tab.query_one.side_effect = lambda selector, _: {
            "#whois-domain": domain_input,
            "#whois-status": status_lbl,
            "#btn-whois-lookup": MagicMock(),
            "#btn-whois-check": MagicMock(),
            "#whois-server": MagicMock()
        }[selector]

        self.tab.output_log = MagicMock(spec=RichLog)
        self.mock_manager.check_availability.return_value = {
            "available": False,
            "output": "Domain is taken"
        }

        await self.tab.action_check()

        self.mock_manager.check_availability.assert_called_once_with("google.com")
        status_lbl.update.assert_called_with("❌ Domain 'google.com' appears to be TAKEN (or status unknown).")
        self.tab.notify.assert_called_with("Domain 'google.com' appears to be TAKEN.", title="Whois Check", severity="warning")
        self.tab.output_log.write.assert_any_call("Domain is taken")
