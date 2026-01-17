import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.auditor = SecurityAuditor(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_bandit_not_installed(self, mock_run, mock_which):
        mock_which.return_value = None
        findings = self.auditor.run_bandit()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "error")
        self.assertIn("Bandit is not installed", findings[0]["message"])

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_bandit_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        mock_output = {
            "results": [
                {
                    "issue_severity": "MEDIUM",
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_text": "Use of assertive detected",
                    "code": "assert True",
                    "issue_cwe": {"link": "https://example.com"}
                }
            ]
        }
        mock_run.return_value = MagicMock(stdout=json.dumps(mock_output), returncode=1)

        findings = self.auditor.run_bandit()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["tool"], "bandit")
        self.assertEqual(findings[0]["severity"], "MEDIUM")
        self.assertEqual(findings[0]["file"], "test.py")

    def test_scan_secrets(self):
        # Create a file with a fake secret
        secret_file = self.project_dir / "config.py"
        with open(secret_file, "w") as f:
            f.write("AWS_ACCESS_KEY_ID = 'AKIA1234567890123456'\n")
            f.write("print('hello')\n")

        findings = self.auditor.scan_secrets()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["tool"], "secret-scanner")
        self.assertEqual(findings[0]["severity"], "HIGH")
        self.assertIn("Potential AWS Access Key detected", findings[0]["message"])
        self.assertIn("AKIA****************", findings[0]["snippet"]) # Check masking

    def test_scan_secrets_skip_dirs(self):
        # Create a secret in .venv
        venv_dir = self.project_dir / ".venv"
        venv_dir.mkdir()
        secret_file = venv_dir / "lib.py"
        with open(secret_file, "w") as f:
            f.write("AWS_ACCESS_KEY_ID = 'AKIA1234567890123456'\n")

        findings = self.auditor.scan_secrets()
        self.assertEqual(len(findings), 0)

if __name__ == "__main__":
    unittest.main()
