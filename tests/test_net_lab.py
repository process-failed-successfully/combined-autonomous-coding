import unittest
from unittest.mock import MagicMock, patch
from shared.net_lab import NetLabManager


class TestNetLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = NetLabManager()

    @patch("socket.create_connection")
    def test_scan_ports_open(self, mock_create_connection):
        # Setup mock to succeed (context manager)
        mock_sock = MagicMock()
        mock_create_connection.return_value.__enter__.return_value = mock_sock

        results = self.manager.scan_ports("localhost", [80])
        self.assertEqual(results[80], "Open")
        mock_create_connection.assert_called_with(("localhost", 80), timeout=0.5)

    @patch("socket.create_connection")
    def test_scan_ports_closed(self, mock_create_connection):
        # Setup mock to raise ConnectionRefusedError
        mock_create_connection.side_effect = ConnectionRefusedError

        results = self.manager.scan_ports("localhost", [80])
        self.assertEqual(results[80], "Closed")

    @patch("socket.gethostbyname_ex")
    def test_dns_lookup_a(self, mock_gethostbyname_ex):
        mock_gethostbyname_ex.return_value = ("example.com", [], ["1.2.3.4"])

        results = self.manager.dns_lookup("example.com", "A")
        self.assertEqual(results["A"], ["1.2.3.4"])

    @patch("requests.head")
    def test_http_head(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_head.return_value = mock_response

        result = self.manager.http_head("http://example.com")
        self.assertEqual(result["status_code"], 200)
        self.assertEqual(result["headers"]["Content-Type"], "text/html")

    @patch("subprocess.call")
    def test_ping_success(self, mock_call):
        mock_call.return_value = 0
        self.assertTrue(self.manager.ping("localhost"))

    @patch("subprocess.call")
    def test_ping_failure(self, mock_call):
        mock_call.return_value = 1
        self.assertFalse(self.manager.ping("localhost"))

    @patch("subprocess.run")
    def test_traceroute_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "traceroute to example.com (1.2.3.4), 30 hops max\n 1  1.2.3.4  1.0 ms"
        mock_run.return_value = mock_result

        result = self.manager.traceroute("example.com")
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], mock_result.stdout)

    @patch("subprocess.run")
    def test_traceroute_failure(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error tracerouting"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = self.manager.traceroute("example.com")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Error tracerouting")

    @patch("requests.get")
    def test_get_ip_info(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "1.2.3.4"
        mock_get.return_value = mock_response

        # Mock socket for local IP
        with patch("socket.socket") as mock_socket:
            mock_sock_instance = MagicMock()
            mock_socket.return_value.__enter__.return_value = mock_sock_instance
            mock_sock_instance.getsockname.return_value = ["192.168.1.10", 12345]

            info = self.manager.get_ip_info()
            self.assertEqual(info["public_ip"], "1.2.3.4")
            self.assertEqual(info["local_ip"], "192.168.1.10")

    @patch("sys.exit", side_effect=SystemExit)
    @patch("shared.tui.AgentTUI.run")
    def test_run_net_lab_logic_tui(self, mock_run, mock_exit):
        from shared.net_lab import run_net_lab_logic
        import argparse
        from pathlib import Path

        args = argparse.Namespace(action="tui", project_dir=Path("."))

        with self.assertRaises(SystemExit):
            run_net_lab_logic(args)

        mock_run.assert_called_once()
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
