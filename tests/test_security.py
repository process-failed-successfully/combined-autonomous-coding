import unittest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.auditor = SecurityAuditor(self.project_dir)

    @patch("shared.security.os.walk")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.stat")
    def test_scan_secrets_aws_key(self, mock_stat, mock_read_text, mock_walk):
        # Setup mock file system
        mock_walk.return_value = [
            (str(self.project_dir), [], ["config.py"])
        ]

        # Mock file content with a fake AWS key
        mock_read_text.return_value = "aws_access_key_id = 'AKIAIOSFODNN7EXAMPLE'"
        mock_stat.return_value.st_size = 100

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "secret")
        self.assertIn("AWS Access Key", findings[0]["description"])
        self.assertIn("AKIA***", findings[0]["snippet"])

    @patch("shared.security.os.walk")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.stat")
    def test_scan_secrets_generic_key(self, mock_stat, mock_read_text, mock_walk):
        mock_walk.return_value = [
            (str(self.project_dir), [], ["api.js"])
        ]

        mock_read_text.return_value = "const apiKey = '1234567890abcdef1234567890abcdef';"
        mock_stat.return_value.st_size = 100

        findings = self.auditor.scan_secrets()

        self.assertEqual(len(findings), 1)
        self.assertIn("Generic API Key", findings[0]["description"])

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_sast_bandit(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        # Mock bandit output
        mock_run.return_value.stdout = """
        {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_text": "Possible hardcoded password",
                    "filename": "main.py",
                    "line_number": 10,
                    "code": "password = '123'"
                }
            ]
        }
        """

        # Mock existence of python files
        with patch("pathlib.Path.glob", return_value=[Path("main.py")]):
             findings = self.auditor.run_sast()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "sast")
        self.assertEqual(findings[0]["tool"], "bandit")
        self.assertEqual(findings[0]["severity"], "HIGH")

    @patch("shutil.which")
    def test_run_sast_no_bandit(self, mock_which):
        mock_which.return_value = None

        with patch("pathlib.Path.glob", return_value=[Path("main.py")]):
            findings = self.auditor.run_sast()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "warning")
        self.assertIn("Bandit not found", findings[0]["description"])

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("pathlib.Path.exists")
    def test_run_dependency_check_npm(self, mock_exists, mock_run, mock_which):
        mock_exists.return_value = True # package.json exists
        mock_which.return_value = "/usr/bin/npm"

        # Mock npm audit output (v7+ format)
        mock_run.return_value.stdout = """
        {
            "vulnerabilities": {
                "lodash": {
                    "severity": "high",
                    "via": [{"title": "Prototype Pollution"}]
                }
            }
        }
        """

        findings = self.auditor.run_dependency_check()

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "dependency")
        self.assertEqual(findings[0]["tool"], "npm audit")
        self.assertEqual(findings[0]["severity"], "HIGH")
        self.assertIn("lodash", findings[0]["description"])

if __name__ == "__main__":
    unittest.main()
