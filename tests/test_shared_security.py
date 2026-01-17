import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import json

from shared.security import SecurityAuditor, SecurityReport, SecurityFinding

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.auditor = SecurityAuditor(self.project_dir)

    def test_init(self):
        self.assertEqual(self.auditor.project_dir, self.project_dir)
        self.assertIsInstance(self.auditor.report, SecurityReport)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_scan_static_no_bandit(self, mock_subprocess, mock_which):
        mock_which.return_value = None
        self.auditor.scan_static()
        mock_subprocess.assert_not_called()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_scan_static_run(self, mock_subprocess, mock_which):
        mock_which.return_value = "/usr/bin/bandit"

        # Mock bandit output
        bandit_output = {
            "results": [
                {
                    "issue_severity": "HIGH",
                    "issue_text": "Use of assert detected.",
                    "filename": "/tmp/test_project/main.py",
                    "line_number": 10,
                    "code": "assert True",
                    "more_info": "http://bandit.readthedocs.io/"
                }
            ]
        }

        mock_subprocess.return_value = MagicMock(
            stdout=json.dumps(bandit_output),
            stderr="",
            returncode=1
        )

        self.auditor.scan_static(severity="medium")

        self.assertEqual(len(self.auditor.report.findings), 1)
        finding = self.auditor.report.findings[0]
        self.assertEqual(finding.type, "static")
        self.assertEqual(finding.severity, "HIGH")
        self.assertEqual(finding.file_path, "main.py")

    @patch("shared.security.SecurityAuditor._list_files")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="AWS_ACCESS_KEY_ID = 'AKIA1234567890123456'")
    def test_scan_secrets(self, mock_open, mock_list_files):
        # Mock file listing
        mock_file = MagicMock() # Use MagicMock instead of actual Path object to mock stat
        # Mocking stat().st_size to be small
        mock_file.stat.return_value.st_size = 100
        mock_file.relative_to.return_value = Path("config.py")

        mock_list_files.return_value = [mock_file]

        self.auditor.scan_secrets()

        self.assertEqual(len(self.auditor.report.findings), 1)
        finding = self.auditor.report.findings[0]
        self.assertEqual(finding.type, "secret")
        self.assertEqual(finding.severity, "HIGH")
        self.assertIn("AWS Access Key", finding.description)
        self.assertIn("AKIA************3456", finding.code)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_list_files_git(self, mock_subprocess, mock_which):
        mock_which.return_value = "/usr/bin/git"
        # Mock .git existing
        with patch.object(Path, "exists", return_value=True):
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="main.py\nshared/utils.py"
            )

            # Mock Path.is_file to always return True
            with patch.object(Path, "is_file", return_value=True):
                files = self.auditor._list_files()
                self.assertEqual(len(files), 2)
                self.assertEqual(files[0], self.project_dir / "main.py")

if __name__ == "__main__":
    unittest.main()
