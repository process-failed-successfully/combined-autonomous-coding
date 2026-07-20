import unittest
from unittest.mock import patch, MagicMock
import json
from shared.osv_lab import OsvLabManager, run_osv_lab_logic


class TestOsvLab(unittest.TestCase):
    def setUp(self):
        self.manager = OsvLabManager()

    @patch('shared.osv_lab.requests.post')
    def test_query_package_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"vulns": [{"id": "CVE-2024-1234"}]}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.manager.query_package("jinja2", "PyPI")
        self.assertEqual(result, {"vulns": [{"id": "CVE-2024-1234"}]})
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json'], {"package": {"name": "jinja2", "ecosystem": "PyPI"}})

    @patch('shared.osv_lab.requests.post')
    def test_query_package_with_version(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"vulns": []}
        mock_post.return_value = mock_response

        result = self.manager.query_package("requests", "PyPI", "2.31.0")
        self.assertEqual(result, {"vulns": []})
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json'], {"package": {"name": "requests", "ecosystem": "PyPI"}, "version": "2.31.0"})

    def test_format_vulnerability(self):
        sample_vuln = {
            "id": "GHSA-123",
            "aliases": ["CVE-2023-456"],
            "summary": "Sample Vuln",
            "details": "This is a detailed description of the vulnerability.",
            "severity": [{"type": "CVSS_V3", "score": "CVSS:3.1/AV:N/AC:L"}],
            "affected": [
                {"ranges": [{"events": [{"introduced": "0"}, {"fixed": "1.2.3"}]}]}
            ]
        }
        output = self.manager.format_vulnerability(sample_vuln)
        self.assertIn("ID: GHSA-123", output)
        self.assertIn("Aliases: CVE-2023-456", output)
        self.assertIn("Severity: CVSS:3.1/AV:N/AC:L", output)
        self.assertIn("Summary: Sample Vuln", output)
        self.assertIn("Fixed in: 1.2.3", output)

    @patch('shared.osv_lab.sys.exit')
    @patch('shared.osv_lab.print')
    @patch('shared.osv_lab.OsvLabManager.query_package')
    def test_cli_json_output(self, mock_query, mock_print, mock_exit):
        mock_query.return_value = {"vulns": [{"id": "CVE-TEST"}]}

        class Args:
            package = "test-pkg"
            ecosystem = "PyPI"
            version = None
            json = True
            tui = False

        run_osv_lab_logic(Args())

        mock_print.assert_called_once()
        called_arg = mock_print.call_args[0][0]
        parsed = json.loads(called_arg)
        self.assertEqual(parsed, {"vulns": [{"id": "CVE-TEST"}]})


if __name__ == '__main__':
    unittest.main()
