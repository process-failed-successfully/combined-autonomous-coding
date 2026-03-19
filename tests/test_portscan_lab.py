import unittest
from unittest.mock import patch, MagicMock
import asyncio
import sys
import io
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.portscan_lab import PortScanManager, parse_port_range, run_portscan_cli_logic

class TestPortScanLab(unittest.IsolatedAsyncioTestCase):

    def test_parse_port_range(self):
        self.assertEqual(parse_port_range("80"), (80, 80))
        self.assertEqual(parse_port_range("1-100"), (1, 100))

        with self.assertRaises(ValueError):
            parse_port_range("invalid")

        with self.assertRaises(ValueError):
            parse_port_range("1-invalid")

    @patch('asyncio.open_connection')
    @patch('asyncio.wait_for')
    async def test_check_port_open(self, mock_wait_for, mock_open_conn):
        from unittest.mock import AsyncMock
        mock_reader = MagicMock()
        mock_writer = AsyncMock()

        # Simulate open_connection success
        mock_open_conn.return_value = (mock_reader, mock_writer)

        # Simulate wait_for success
        mock_wait_for.return_value = (mock_reader, mock_writer)

        manager = PortScanManager()
        port, is_open, service = await manager.check_port("127.0.0.1", 80)

        self.assertEqual(port, 80)
        self.assertTrue(is_open)
        self.assertEqual(service, "HTTP")

    @patch('asyncio.open_connection')
    async def test_check_port_closed(self, mock_open_conn):
        # Simulate connection refused
        mock_open_conn.side_effect = ConnectionRefusedError()

        manager = PortScanManager()
        port, is_open, service = await manager.check_port("127.0.0.1", 80)

        self.assertEqual(port, 80)
        self.assertFalse(is_open)
        self.assertEqual(service, "")

    @patch('shared.portscan_lab.PortScanManager.check_port')
    async def test_scan_ports(self, mock_check_port):
        # Mock responses: 80 open, 81 closed
        async def side_effect(host, port, timeout):
            if port == 80:
                return 80, True, "HTTP"
            return port, False, ""

        mock_check_port.side_effect = side_effect

        manager = PortScanManager()
        results = await manager.scan_ports("127.0.0.1", 80, 81)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["port"], "80")
        self.assertEqual(results[0]["service"], "HTTP")

    @patch('shared.portscan_lab.PortScanManager.scan_ports')
    async def test_run_portscan_cli_logic(self, mock_scan_ports):
        mock_scan_ports.return_value = [{"port": "80", "service": "HTTP"}]

        class Args:
            host = "127.0.0.1"
            ports = "80-80"
            timeout = 1.0
            concurrency = 100

        args = Args()

        # Capture stdout
        captured_output = io.StringIO()
        sys.stdout = captured_output

        success = await run_portscan_cli_logic(args)

        sys.stdout = sys.__stdout__

        self.assertTrue(success)
        self.assertIn("Scanning 127.0.0.1", captured_output.getvalue())
        self.assertIn("80", captured_output.getvalue())
        self.assertIn("HTTP", captured_output.getvalue())

if __name__ == '__main__':
    unittest.main()
