import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.security_fix import SecurityRemediator


class TestSecurityFix(unittest.TestCase):

    def setUp(self):
        self.project_dir = Path("/fake/project")
        self.remediator = SecurityRemediator(self.project_dir)

    @patch("shared.security_fix.SecurityRemediator._run_tests")
    @patch("shared.dependencies.DependencyUpdater.update_dependency")
    @patch("shared.dependencies.DependencyAnalyzer.get_latest_pypi_version")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.write_text")
    def test_remediate_python_success(self, mock_write, mock_read, mock_exists, mock_get_latest, mock_update, mock_run_tests):
        # Setup
        findings = [{
            "type": "dependency",
            "tool": "OSV (PyPI)",
            "description": "Vulnerability in requests",
            "snippet": "Upgrade requests",
            "file": "requirements.txt"
        }]

        mock_get_latest.return_value = "2.31.0"
        mock_exists.return_value = True
        mock_read.return_value = "requests==2.0.0"
        mock_update.return_value = True
        mock_run_tests.return_value = True  # Tests pass

        # Execute
        results = self.remediator.run_remediation(findings, yes=True)

        # Verify
        self.assertIn("requests", results["fixed"])
        self.assertEqual(len(results["failed"]), 0)
        self.assertEqual(len(results["skipped"]), 0)

        mock_update.assert_called_once()
        mock_run_tests.assert_called_once()
        # Verify NO revert (write_text should not be called with original content)
        # Note: update_dependency might write text, but we mocked it.
        # But if tests fail, run_remediation calls write_text to revert.
        mock_write.assert_not_called()

    @patch("shared.security_fix.SecurityRemediator._run_tests")
    @patch("shared.dependencies.DependencyUpdater.update_dependency")
    @patch("shared.dependencies.DependencyAnalyzer.get_latest_pypi_version")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.write_text")
    def test_remediate_python_test_fail_revert(self, mock_write, mock_read, mock_exists, mock_get_latest, mock_update, mock_run_tests):
        # Setup
        findings = [{
            "type": "dependency",
            "tool": "OSV (PyPI)",
            "snippet": "Upgrade requests",
            "file": "requirements.txt"
        }]

        mock_get_latest.return_value = "2.31.0"
        mock_exists.return_value = True
        original_content = "requests==2.0.0"
        mock_read.return_value = original_content
        mock_update.return_value = True
        mock_run_tests.return_value = False  # Tests FAIL

        # Execute
        results = self.remediator.run_remediation(findings, yes=True)

        # Verify
        self.assertIn("requests", results["failed"])

        mock_update.assert_called_once()
        mock_run_tests.assert_called_once()

        # Verify revert happened
        mock_write.assert_called_with(original_content)

    @patch("shared.security_fix.SecurityRemediator._run_tests")
    @patch("shared.dependencies.DependencyAnalyzer.get_latest_npm_version")
    def test_remediate_node_dry_run(self, mock_get_latest, mock_run_tests):
        # Setup
        findings = [{
            "type": "dependency",
            "tool": "npm audit",
            "description": "Vulnerability in lodash",
            "file": "package.json",
            "snippet": "Upgrade lodash"
        }]

        mock_get_latest.return_value = "4.17.21"

        # Execute
        results = self.remediator.run_remediation(findings, dry_run=True, yes=True)

        # Verify
        self.assertIn("lodash", results["fixed"])  # In dry run we count valid candidates as fixed/processed
        mock_run_tests.assert_not_called()

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_tests_command(self, mock_which, mock_run):
        mock_which.return_value = "/usr/bin/pytest"
        mock_run.return_value = MagicMock(returncode=0)

        success = self.remediator._run_tests("python")

        self.assertTrue(success)
        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["pytest"])

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_run_tests_fallback(self, mock_which, mock_run):
        # Simulate pytest NOT installed
        def which_side_effect(cmd):
            return None
        mock_which.side_effect = which_side_effect

        mock_run.return_value = MagicMock(returncode=0)

        import sys
        success = self.remediator._run_tests("python")

        self.assertTrue(success)
        mock_run.assert_called()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, [sys.executable, "-m", "unittest", "discover"])


if __name__ == '__main__':
    unittest.main()
