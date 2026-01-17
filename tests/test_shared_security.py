
import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.security import SecurityAuditor

class TestSharedSecurity(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.auditor = SecurityAuditor()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_secrets_aws_access_key(self):
        """Test detection of AWS Access Keys."""
        secret_file = self.project_dir / "aws_config.txt"
        # AKIA followed by 16 chars
        fake_key = "AKIA" + "0123456789ABCDEF"
        with open(secret_file, "w") as f:
            f.write(f"aws_access_key_id = {fake_key}\n")

        findings = self.auditor.scan_secrets(self.project_dir)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "SECRET_AWS_ACCESS_KEY")
        # Masking: AKIA... -> AK****************EF
        # We can just check for asterisks and the start/end
        self.assertIn("AK**", findings[0]["snippet"])
        self.assertIn("EF", findings[0]["snippet"])

    def test_scan_secrets_generic_api_key(self):
        """Test detection of generic API keys."""
        secret_file = self.project_dir / "config.json"
        fake_key = "abcdef1234567890abcdef1234567890" # 32 chars
        with open(secret_file, "w") as f:
            # Matches "key": "value" pattern
            f.write(f'{{"api_key": "{fake_key}"}}\n')

        findings = self.auditor.scan_secrets(self.project_dir)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["check_id"], "SECRET_GENERIC_API_KEY")
        self.assertIn("ab**", findings[0]["snippet"]) # Masked

    def test_scan_secrets_skip_dirs(self):
        """Test that specified directories are skipped."""
        venv_dir = self.project_dir / ".venv"
        venv_dir.mkdir()
        secret_file = venv_dir / "lib.py"
        fake_key = "AKIA" + "0123456789ABCDEF"
        with open(secret_file, "w") as f:
            f.write(f"key = {fake_key}")

        findings = self.auditor.scan_secrets(self.project_dir)
        self.assertEqual(len(findings), 0)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_bandit_installed(self, mock_run, mock_which):
        """Test running bandit when it is installed."""
        mock_which.return_value = "/usr/bin/bandit"

        # Mock successful bandit run with findings
        mock_result = MagicMock()
        mock_result.returncode = 1 # Bandit exits with 1 on issues
        mock_result.stdout = json.dumps({
            "results": [{
                "issue_severity": "HIGH",
                "issue_text": "Hardcoded password",
                "filename": "main.py",
                "line_number": 10
            }]
        })
        mock_run.return_value = mock_result

        findings = self.auditor.run_bandit(self.project_dir)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "bandit")
        self.assertEqual(findings[0]["severity"], "HIGH")

    @patch("shutil.which")
    def test_run_bandit_not_installed(self, mock_which):
        """Test behavior when bandit is not installed."""
        mock_which.return_value = None

        findings = self.auditor.run_bandit(self.project_dir)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "error")
        self.assertIn("not installed", findings[0]["issue_text"])

    @patch("shared.security.SecurityAuditor.run_bandit")
    @patch("shared.security.SecurityAuditor.scan_secrets")
    def test_run_security_scan_all(self, mock_secrets, mock_bandit):
        """Test the orchestration method."""
        mock_secrets.return_value = [{"type": "secret", "severity": "HIGH"}]
        mock_bandit.return_value = [{"type": "bandit", "severity": "LOW"}]

        result = self.auditor.run_security_scan(self.project_dir, scan_type="all")

        self.assertEqual(len(result["findings"]), 2)
        self.assertEqual(result["summary"]["total"], 2)
        self.assertEqual(result["summary"]["high"], 1)
        self.assertEqual(result["summary"]["low"], 1)

if __name__ == "__main__":
    unittest.main()
