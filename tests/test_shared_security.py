"""
Tests for Shared Security Utilities
===================================
"""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import json
from pathlib import Path
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        # We don't initialize auditor here to allow tests to patch shutil.which first

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_bandit_success(self, mock_which, mock_subprocess):
        """Test running bandit successfully."""
        mock_which.return_value = "/usr/bin/bandit"
        auditor = SecurityAuditor(self.project_dir)

        mock_output = {
            "results": [
                {"issue_text": "Use of exec detected", "filename": "test.py", "line_number": 10, "issue_severity": "HIGH"}
            ],
            "metrics": {}
        }

        mock_subprocess.return_value = MagicMock(
            stdout=json.dumps(mock_output),
            stderr="",
            returncode=1 # Bandit returns 1 on issues
        )

        result = auditor.run_bandit()

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["issue_text"], "Use of exec detected")

        # Verify command arguments
        args = mock_subprocess.call_args[0][0]
        self.assertIn("/usr/bin/bandit", args)
        self.assertIn("--severity-level", args)
        self.assertIn("low", args) # Default

    @patch("shutil.which")
    def test_run_bandit_not_found(self, mock_which):
        """Test behavior when bandit is missing."""
        mock_which.return_value = None
        auditor = SecurityAuditor(self.project_dir)

        result = auditor.run_bandit()
        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_scan_secrets_regex(self):
        """Test that scan_secrets finds patterns."""
        auditor = SecurityAuditor(self.project_dir)
        # Create a file with a fake secret
        secret_file = self.project_dir / "config.py"
        with open(secret_file, "w") as f:
            f.write("aws_secret_access_key = 'ABCD1234ABCD1234ABCD1234ABCD1234ABCD1234'\n")
            f.write("some_other_code = True\n")

        # Create a safe file
        safe_file = self.project_dir / "safe.py"
        with open(safe_file, "w") as f:
            f.write("print('Hello world')\n")

        # Mock _get_files_to_scan to return these files (avoiding git/os.walk complexity in this unit test)
        with patch.object(auditor, "_get_files_to_scan", return_value=[secret_file, safe_file]):
            findings = auditor.scan_secrets()

            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["type"], "AWS Secret Key")
            self.assertEqual(findings[0]["file"], "config.py")
            self.assertEqual(findings[0]["line"], 1)

    def test_audit_aggregation(self):
        """Test that audit aggregates results correctly."""
        auditor = SecurityAuditor(self.project_dir)
        with patch.object(auditor, "run_bandit") as mock_bandit:
            with patch.object(auditor, "scan_secrets") as mock_secrets:
                mock_bandit.return_value = {"results": [{"id": 1}]}
                mock_secrets.return_value = [{"type": "secret"}]

                report = auditor.audit(scan_type="all")

                self.assertEqual(report["summary"]["total_issues"], 2)
                self.assertIsNotNone(report["bandit"])
                self.assertIsNotNone(report["secrets"])

if __name__ == "__main__":
    unittest.main()
