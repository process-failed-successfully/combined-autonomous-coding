import unittest
from unittest.mock import MagicMock, patch
import asyncio
from textual.widgets import Input, RichLog, DataTable, Label
# Import the class under test
from shared.tui_cidr import CidrLabTab

class TestCidrLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch CidrLabManager at the source where it is imported in tui_cidr
        self.patcher = patch("shared.tui_cidr.CidrLabManager")
        self.MockManager = self.patcher.start()

        # Instantiate the tab
        self.tab = CidrLabTab()
        self.mock_manager = self.MockManager.return_value
        # Ensure the tab uses our mock instance
        self.tab.manager = self.mock_manager

        # Mock Textual UI methods
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_run_info_success(self):
        # Mock Inputs
        cidr_input = MagicMock(spec=Input)
        cidr_input.value = "192.168.1.0/24"
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#info-cidr": return cidr_input
            if selector == "#info-table": return table
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.get_info.return_value = {
            "cidr": "192.168.1.0/24",
            "netmask": "255.255.255.0",
            "first_host": "192.168.1.1"
        }

        # Run
        await self.tab.run_info()

        # Verify
        self.mock_manager.get_info.assert_called_with("192.168.1.0/24")
        table.clear.assert_called()
        self.assertEqual(table.add_row.call_count, 3) # cidr, netmask, first_host
        self.tab.notify.assert_called_with("Info loaded.")

    async def test_run_subnet_success(self):
        # Mock Inputs
        cidr_input = MagicMock(spec=Input)
        cidr_input.value = "10.0.0.0/8"
        prefix_input = MagicMock(spec=Input)
        prefix_input.value = "16"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#subnet-cidr": return cidr_input
            if selector == "#subnet-prefix": return prefix_input
            if selector == "#subnet-log": return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.subnet.return_value = {
            "count": 256,
            "subnets": ["10.0.0.0/16", "10.1.0.0/16"]
        }

        # Run
        await self.tab.run_subnet()

        # Verify
        self.mock_manager.subnet.assert_called_with("10.0.0.0/8", 16)
        log.write.assert_called()
        args, _ = log.write.call_args_list[0]
        self.assertIn("Calculating", args[0])
        self.tab.notify.assert_called_with("Calculation complete.")

    async def test_run_contains_true(self):
        # Mock Inputs
        cidr_input = MagicMock(spec=Input)
        cidr_input.value = "192.168.0.0/16"
        target_input = MagicMock(spec=Input)
        target_input.value = "192.168.1.5"
        lbl = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#contains-cidr": return cidr_input
            if selector == "#contains-target": return target_input
            if selector == "#lbl-contains-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.contains.return_value = {
            "contains": True,
            "container": "192.168.0.0/16",
            "target": "192.168.1.5"
        }

        # Run
        await self.tab.run_contains()

        # Verify
        self.mock_manager.contains.assert_called_with("192.168.0.0/16", "192.168.1.5")
        lbl.update.assert_called()
        args, _ = lbl.update.call_args
        self.assertIn("YES", args[0])

    async def test_run_overlap_true(self):
        # Mock Inputs
        cidr1_input = MagicMock(spec=Input)
        cidr1_input.value = "10.0.0.0/8"
        cidr2_input = MagicMock(spec=Input)
        cidr2_input.value = "10.1.0.0/16"
        lbl = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#overlap-cidr1": return cidr1_input
            if selector == "#overlap-cidr2": return cidr2_input
            if selector == "#lbl-overlap-result": return lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.overlaps.return_value = {
            "overlaps": True,
            "cidr1": "10.0.0.0/8",
            "cidr2": "10.1.0.0/16"
        }

        # Run
        await self.tab.run_overlap()

        # Verify
        self.mock_manager.overlaps.assert_called_with("10.0.0.0/8", "10.1.0.0/16")
        lbl.update.assert_called()
        args, _ = lbl.update.call_args
        self.assertIn("OVERLAP DETECTED", args[0])

if __name__ == "__main__":
    unittest.main()
