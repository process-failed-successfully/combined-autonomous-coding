import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from textual.widgets import Input, RichLog, Button
from shared.tui_cert import CertLabTab

class TestCertLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = CertLabTab(self.project_dir)

        # Mock the manager
        self.tab.manager = MagicMock()

        # Mock notify
        self.tab.notify = MagicMock()

    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_inspect_file(self, mock_to_thread):
        """Test inspecting a file."""
        # Setup mocks
        mock_input = MagicMock(spec=Input)
        mock_input.value = "test.pem"

        mock_log = MagicMock(spec=RichLog)

        # Mock query_one
        self.tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#cert-target": mock_input,
            "#cert-inspect-log": mock_log
        }.get(selector))

        # Setup manager return
        details = {
            "Subject": {"CN": "Test"},
            "Issuer": {"CN": "Issuer"},
            "Not Before": "2023-01-01",
            "Not After": "2024-01-01",
            "Days Remaining": 100,
            "SANs": ["test.com"],
            "Serial Number": 12345,
            "Fingerprint (SHA256)": "deadbeef"
        }
        mock_to_thread.return_value = details

        # Patch Path.exists/is_file
        with patch("pathlib.Path.exists", return_value=True), \
             patch("pathlib.Path.is_file", return_value=True):

            await self.tab.on_inspect()

        # Verification
        # Check that to_thread was called with the manager method
        mock_to_thread.assert_called()
        args, _ = mock_to_thread.call_args
        self.assertEqual(args[0], self.tab.manager.inspect_file)
        self.assertEqual(args[1], Path("test.pem"))

        mock_log.write.assert_any_call(f"Inspecting test.pem...")
        mock_log.write.assert_any_call("\n[bold underline]Certificate Info[/bold underline]")
        mock_log.write.assert_any_call("  CN: [cyan]Test[/cyan]")

    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_inspect_host(self, mock_to_thread):
        """Test inspecting a host."""
        # Setup mocks
        mock_input = MagicMock(spec=Input)
        mock_input.value = "google.com:443"

        mock_log = MagicMock(spec=RichLog)

        self.tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#cert-target": mock_input,
            "#cert-inspect-log": mock_log
        }.get(selector))

        details = {"Subject": {}, "Issuer": {}}
        mock_to_thread.return_value = details

        # Patch Path.exists to False so it falls back to host
        with patch("pathlib.Path.exists", return_value=False):
            await self.tab.on_inspect()

        # Verification
        mock_to_thread.assert_called()
        args, _ = mock_to_thread.call_args
        self.assertEqual(args[0], self.tab.manager.inspect_host)
        self.assertEqual(args[1], "google.com")
        self.assertEqual(args[2], 443)

        mock_log.write.assert_any_call("Connecting to google.com:443...")

    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_generate_cert(self, mock_to_thread):
        """Test generating a certificate."""
        # Setup mocks
        mock_cn = MagicMock(spec=Input)
        mock_cn.value = "localhost"

        mock_sans = MagicMock(spec=Input)
        mock_sans.value = "127.0.0.1"

        mock_days = MagicMock(spec=Input)
        mock_days.value = "365"

        mock_log = MagicMock(spec=RichLog)

        self.tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#cert-cn": mock_cn,
            "#cert-sans": mock_sans,
            "#cert-days": mock_days,
            "#cert-gen-log": mock_log
        }.get(selector))

        mock_to_thread.return_value = (Path("cert.pem"), Path("key.pem"))

        await self.tab.on_generate()

        # Verification
        # Since on_generate uses a closure 'do_gen', we can't easily check to_thread args directly for the closure content
        # unless we execute it. But mock_to_thread just returns the value.
        # However, we can trust that if the success message is logged, the logic flow reached the end.

        mock_to_thread.assert_called()
        self.tab.notify.assert_called_with("Certificate generated.")
        mock_log.write.assert_any_call("[bold green]Success![/bold green]")

if __name__ == "__main__":
    unittest.main()
