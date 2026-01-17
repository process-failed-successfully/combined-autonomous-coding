import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from shared.security import SecurityAuditor

class TestSecurityAuditor(unittest.TestCase):

    def setUp(self):
        self.auditor = SecurityAuditor()
        self.project_dir = Path("/fake/project")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_bandit_success(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/bandit"
        mock_run.return_value = MagicMock(
            stdout=json.dumps({"results": [{"test_id": "B101", "issue_text": "Use of assert detected."}]}),
            returncode=0
        )

        results = self.auditor.run_bandit(self.project_dir)

        self.assertIn("results", results)
        self.assertEqual(len(results["results"]), 1)
        self.assertEqual(results["results"][0]["test_id"], "B101")

        # Verify call args
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args[0][0]
        self.assertIn("/usr/bin/bandit", cmd_args)
        self.assertIn("--severity-level", cmd_args)
        self.assertIn("medium", cmd_args)

    @patch("shutil.which")
    def test_run_bandit_not_found(self, mock_which):
        mock_which.return_value = None
        results = self.auditor.run_bandit(self.project_dir)
        self.assertIn("error", results)
        self.assertIn("Bandit tool not found", results["error"])

    @patch("shared.security.subprocess.run")
    @patch("shared.security.Path.read_text")
    @patch("shared.security.Path.exists")
    @patch("shared.security.Path.is_file")
    @patch("shared.security.Path.is_dir")
    @patch("shared.security.Path.stat")
    def test_scan_secrets(self, mock_stat, mock_is_dir, mock_is_file, mock_exists, mock_read_text, mock_subprocess):
        # Mock git ls-files failure to force os.walk fallback, or mock git ls-files success.
        # Let's mock git ls-files success for simplicity as it's the primary path.
        mock_subprocess.side_effect = [
            MagicMock(stdout="/usr/bin/git"), # which git
            MagicMock(returncode=0, stdout="config.py\nmain.py") # git ls-files
        ]

        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = True # For .git directory check
        mock_stat.return_value.st_size = 100

        # main.py content with a fake secret
        mock_read_text.side_effect = [
            "nothing here", # config.py
            "aws_key = 'AKIA1234567890123456'" # main.py
        ]

        findings = self.auditor.scan_secrets(self.project_dir)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "AWS Access Key")
        # Expect masked value
        self.assertIn("AKIA************3456", findings[0]["match"])

    def test_audit_project(self):
        with patch.object(self.auditor, 'run_bandit') as mock_bandit, \
             patch.object(self.auditor, 'scan_secrets') as mock_secrets:

            mock_bandit.return_value = {"results": [{"id": 1}]}
            mock_secrets.return_value = [{"type": "key"}]

            report = self.auditor.audit_project(self.project_dir)

            mock_bandit.assert_called_once()
            mock_secrets.assert_called_once()
            self.assertEqual(report["summary"]["issues_found"], 2)

if __name__ == '__main__':
    unittest.main()
