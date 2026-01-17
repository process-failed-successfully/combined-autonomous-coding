import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import json
import subprocess
from shared.security import SecurityAuditor, SecurityIssue

class TestSecurityAuditor(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.auditor = SecurityAuditor(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("subprocess.run")
    def test_run_bandit_success(self, mock_run):
        # Mock bandit output
        bandit_output = {
            "results": [
                {
                    "test_id": "B101",
                    "issue_text": "Use of assert detected.",
                    "filename": "test.py",
                    "line_number": 10,
                    "issue_severity": "LOW",
                    "issue_confidence": "HIGH",
                    "code": "assert True",
                    "more_info": "https://..."
                }
            ]
        }

        mock_result = MagicMock()
        mock_result.stdout = json.dumps(bandit_output)
        mock_result.returncode = 1 # Bandit returns 1 on issues
        mock_run.return_value = mock_result

        issues = self.auditor.run_bandit()

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].check_id, "B101")
        self.assertEqual(issues[0].severity, "LOW")

        # Verify command arguments
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        self.assertIn("bandit", args)
        self.assertIn("--severity-level", args)

    @patch("subprocess.run")
    def test_run_bandit_no_issues(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"results": []})
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        issues = self.auditor.run_bandit()
        self.assertEqual(len(issues), 0)

    def test_scan_secrets_aws(self):
        # Create a file with a fake AWS key
        secret_file = self.test_dir / "config.py"
        # Pattern: AKIA... (20 chars)
        fake_key = "AKIA" + "0" * 16
        content = f"aws_key = '{fake_key}'"
        secret_file.write_text(content)

        # Mock git call to ensure we use os.walk fallback which finds the file in test_dir
        with patch("subprocess.run") as mock_run:
            # First call checks if git exists (which returns 0), second call fails because not a git repo
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "git":
                    raise subprocess.CalledProcessError(128, cmd)
                return MagicMock()

            mock_run.side_effect = side_effect

            issues = self.auditor.scan_secrets()

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].check_id, "SECRET-SCAN")
        self.assertIn("AWS Access Key", issues[0].description)
        # Check obfuscation - only first 4 chars should be visible
        masked = fake_key[:4] + "*" * (len(fake_key) - 4)
        self.assertIn(masked, issues[0].description)

    def test_scan_secrets_ignored_files(self):
        # Create a file in an ignored directory
        venv_dir = self.test_dir / ".venv"
        venv_dir.mkdir()
        secret_file = venv_dir / "lib.py"
        fake_key = "AKIA" + "0" * 16
        secret_file.write_text(f"key = '{fake_key}'")

        # Mocking git ls-files failure to force os.walk fallback which has our exclusion logic
        with patch("subprocess.run") as mock_run:
            def side_effect(*args, **kwargs):
                cmd = args[0]
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "git":
                    raise subprocess.CalledProcessError(128, cmd)
                return MagicMock()

            mock_run.side_effect = side_effect

            issues = self.auditor.scan_secrets()

        self.assertEqual(len(issues), 0)

if __name__ == "__main__":
    unittest.main()
