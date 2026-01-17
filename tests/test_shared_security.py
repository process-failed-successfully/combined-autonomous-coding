import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import json
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.auditor = SecurityAuditor()
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.security.subprocess.run")
    def test_run_bandit_success(self, mock_subprocess):
        # Mocking successful bandit execution with findings
        mock_output = json.dumps({
            "results": [
                {
                    "issue_text": "Hardcoded password",
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "HIGH",
                    "issue_confidence": "HIGH",
                    "code": "password = '123'",
                    "more_info": "http://bandit.readthedocs.io/"
                }
            ]
        })
        mock_subprocess.return_value = MagicMock(stdout=mock_output, returncode=1)

        result = self.auditor.run_bandit(self.project_dir)

        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["issue_text"], "Hardcoded password")

        # Verify call arguments
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        self.assertIn("bandit", args)
        self.assertIn("-r", args)
        self.assertIn("-f", args)
        self.assertIn("json", args)

    @patch("shared.security.subprocess.run")
    def test_run_bandit_no_issues(self, mock_subprocess):
        # Mocking bandit with no issues
        mock_subprocess.return_value = MagicMock(stdout="{}", returncode=0)

        result = self.auditor.run_bandit(self.project_dir)
        self.assertEqual(result, {})

    @patch("shared.security.subprocess.run")
    def test_run_bandit_not_found(self, mock_subprocess):
        mock_subprocess.side_effect = FileNotFoundError

        result = self.auditor.run_bandit(self.project_dir)
        self.assertIn("error", result)
        self.assertIn("Bandit command not found", result["error"])

    @patch("shared.security.SecurityAuditor._get_git_files")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_file")
    def test_scan_secrets(self, mock_is_file, mock_exists, mock_read_text, mock_get_git_files):
        # Setup mocks
        mock_get_git_files.return_value = ["config.py"]
        mock_exists.return_value = True
        mock_is_file.return_value = True

        # Simulate a file content with a secret.
        # Note: 'AKIA...' matches "AWS Access Key". 'secret = ...' matches "Generic API Key".
        # So this line will generate 2 findings.
        mock_read_text.return_value = "aws_secret = 'AKIAIOSFODNN7EXAMPLE'"

        findings = self.auditor.scan_secrets(self.project_dir)

        self.assertEqual(len(findings), 2)

        # Check that we found at least one AWS key
        aws_finding = next((f for f in findings if "AWS Access Key" in f["issue_text"]), None)
        self.assertIsNotNone(aws_finding)
        self.assertEqual(aws_finding["severity"], "HIGH")

    @patch("shared.security.SecurityAuditor.run_bandit")
    @patch("shared.security.SecurityAuditor.scan_secrets")
    def test_audit_all(self, mock_scan_secrets, mock_run_bandit):
        # bandit uses 'issue_severity', secrets uses 'severity'
        mock_run_bandit.return_value = {"results": [{"issue_text": "Bandit Issue", "issue_severity": "MEDIUM"}]}
        mock_scan_secrets.return_value = [{"issue_text": "Secret Issue", "severity": "HIGH"}]

        report = self.auditor.audit(self.project_dir, scan_type="all")

        self.assertEqual(len(report["findings"]), 2)
        self.assertEqual(report["summary"]["issues"], 2)
        # 100 - 5 (Medium) - 10 (High) = 85
        self.assertEqual(report["summary"]["score"], 85)

if __name__ == "__main__":
    unittest.main()
