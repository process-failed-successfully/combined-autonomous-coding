import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Label, Button, Input, Select, RichLog, Static
from shared.tui_uuid import UuidLabTab

class TestUuidLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_uuid_generation(self):
        """Test generating UUIDs in the TUI."""
        tab = UuidLabTab()

        # Mock widgets
        mock_log = MagicMock(spec=RichLog)
        mock_ver = MagicMock(spec=Select)
        mock_ver.value = 4
        mock_count = MagicMock(spec=Input)
        mock_count.value = "2"
        mock_ns = MagicMock(spec=Input)
        mock_ns.value = ""
        mock_name = MagicMock(spec=Input)
        mock_name.value = ""

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#log-uuid-generate": mock_log,
            "#select-uuid-version": mock_ver,
            "#input-uuid-count": mock_count,
            "#input-uuid-namespace": mock_ns,
            "#input-uuid-name": mock_name
        }.get(selector))

        # Mock notify to prevent NoActiveAppError
        tab.notify = MagicMock()

        # Trigger generate
        tab.on_generate()

        # Check that log.write was called twice (for 2 UUIDs)
        self.assertEqual(mock_log.write.call_count, 2)
        # Check notify called
        # tab.notify is from App or Widget, we might need to mock it if it fails,
        # but Container inherits from Widget which has notify.
        # Since we instantiated UuidLabTab in isolation without an App, notify might fail or do nothing.
        # But we are mocking query_one, so we are fine.

    async def test_uuid_inspect(self):
        """Test inspecting a UUID."""
        tab = UuidLabTab()

        mock_log = MagicMock(spec=RichLog)
        mock_input = MagicMock(spec=Input)
        # Valid v4 UUID
        test_uuid = "123e4567-e89b-12d3-a456-426614174000"
        mock_input.value = test_uuid

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#log-uuid-inspect": mock_log,
            "#input-uuid-inspect": mock_input
        }.get(selector))

        # Mock notify
        tab.notify = MagicMock()

        tab.on_inspect()

        # Check output
        # We expect multiple writes for details
        self.assertTrue(mock_log.write.call_count > 0)
        # Verify it tried to write the UUID
        args, _ = mock_log.write.call_args_list[0]
        self.assertIn(test_uuid, args[0])

    async def test_uuid_validate(self):
        """Test validating a UUID."""
        tab = UuidLabTab()

        mock_lbl = MagicMock(spec=Static)
        mock_input = MagicMock(spec=Input)

        # Valid
        mock_input.value = "123e4567-e89b-12d3-a456-426614174000"

        tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#lbl-uuid-validate-result": mock_lbl,
            "#input-uuid-validate": mock_input
        }.get(selector))

        # Mock notify
        tab.notify = MagicMock()

        tab.on_validate()
        mock_lbl.update.assert_called_with("[bold green]✅ Valid UUID[/bold green]")

        # Invalid
        mock_input.value = "not-a-uuid"
        tab.on_validate()
        mock_lbl.update.assert_called_with("[bold red]❌ Invalid UUID[/bold red]")

if __name__ == "__main__":
    unittest.main()
