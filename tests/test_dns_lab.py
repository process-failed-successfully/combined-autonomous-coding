import unittest
from unittest.mock import MagicMock, patch
from shared.dns_lab import DnsLabManager


class TestDnsLabManager(unittest.TestCase):
    def setUp(self):
        # Patch shutil.which to simulate dig being present
        self.which_patcher = patch('shutil.which', return_value='/usr/bin/dig')
        self.mock_which = self.which_patcher.start()
        self.manager = DnsLabManager()

    def tearDown(self):
        self.which_patcher.stop()

    @patch('subprocess.run')
    def test_lookup_success(self, mock_run):
        # Mock successful dig output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "93.184.216.34\n"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        result = self.manager.lookup("example.com", "A")

        self.assertIn("records", result)
        self.assertEqual(result["records"], ["93.184.216.34"])

        # Verify command construction
        mock_run.assert_called_with(
            ['/usr/bin/dig', '+short', 'A', 'example.com'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_lookup_with_server(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "93.184.216.34\n"
        mock_run.return_value = mock_process

        self.manager.lookup("example.com", "A", server="8.8.8.8")

        mock_run.assert_called_with(
            ['/usr/bin/dig', '+short', 'A', 'example.com', '@8.8.8.8'],
            capture_output=True,
            text=True
        )

    @patch('subprocess.run')
    def test_lookup_failure(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Connection timed out"
        mock_run.return_value = mock_process

        result = self.manager.lookup("example.com")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Connection timed out")

    @patch('subprocess.run')
    def test_lookup_empty(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        result = self.manager.lookup("example.com")
        self.assertEqual(result["records"], [])

    @patch.object(DnsLabManager, 'lookup')
    def test_check_propagation(self, mock_lookup):
        # Mock lookup responses for different servers
        def side_effect(domain, record_type, server=None):
            if server == "8.8.8.8":  # Google
                return {"records": ["1.2.3.4"]}
            elif server == "1.1.1.1":  # Cloudflare
                return {"records": ["1.2.3.4"]}
            else:
                return {"records": []}  # Others not propagated yet

        mock_lookup.side_effect = side_effect

        results = self.manager.check_propagation("example.com")

        self.assertIn("Google", results)
        self.assertEqual(results["Google"], ["1.2.3.4"])
        self.assertIn("Cloudflare", results)
        self.assertEqual(results["Cloudflare"], ["1.2.3.4"])
        self.assertEqual(results["Quad9"], [])

    def test_missing_dig(self):
        with patch('shutil.which', return_value=None):
            manager = DnsLabManager()
            result = manager.lookup("example.com")
            self.assertIn("error", result)
            self.assertIn("dig command not found", result["error"])


if __name__ == '__main__':
    unittest.main()
