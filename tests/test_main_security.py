import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import tempfile
import shutil
import argparse
import json

# It's necessary to add the project root to the path for the import to work
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_security

class TestMainSecurity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_mock_args(self, scan_type="all", severity="medium", output=None):
        return argparse.Namespace(
            project_dir=self.project_dir,
            scan_type=scan_type,
            severity=severity,
            output=output
        )

    @patch('shared.security.SecurityAuditor')
    def test_run_security_clean(self, MockAuditor):
        """Test that run_security passes when no issues found."""
        instance = MockAuditor.return_value
        instance.scan_secrets.return_value = []
        instance.run_bandit.return_value = {"results": []}

        args = self._create_mock_args()

        with self.assertRaises(SystemExit) as cm:
            run_security(args)
        self.assertEqual(cm.exception.code, 0)

        instance.scan_secrets.assert_called_once()
        instance.run_bandit.assert_called_once_with(severity="medium")

    @patch('shared.security.SecurityAuditor')
    def test_run_security_issues_found(self, MockAuditor):
        """Test that run_security fails when issues found."""
        instance = MockAuditor.return_value
        instance.scan_secrets.return_value = [{"type": "Secret", "severity": "HIGH", "file": "f", "line": 1, "snippet": "s"}]
        instance.run_bandit.return_value = {"results": []}

        args = self._create_mock_args()

        with self.assertRaises(SystemExit) as cm:
            run_security(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('shared.security.SecurityAuditor')
    def test_run_security_bandit_only(self, MockAuditor):
        """Test scan_type=bandit."""
        instance = MockAuditor.return_value
        instance.run_bandit.return_value = {"results": []}

        args = self._create_mock_args(scan_type="bandit")

        with self.assertRaises(SystemExit) as cm:
            run_security(args)

        instance.scan_secrets.assert_not_called()
        instance.run_bandit.assert_called_once()

    @patch('shared.security.SecurityAuditor')
    def test_output_json(self, MockAuditor):
        """Test output to JSON file."""
        instance = MockAuditor.return_value
        instance.scan_secrets.return_value = []
        instance.run_bandit.return_value = {"results": []}

        output_file = self.project_dir / "report.json"
        args = self._create_mock_args(output=output_file)

        with self.assertRaises(SystemExit):
            run_security(args)

        self.assertTrue(output_file.exists())
        with open(output_file) as f:
            data = json.load(f)
            self.assertIn("secrets", data)
            self.assertIn("bandit", data)

if __name__ == '__main__':
    unittest.main()
