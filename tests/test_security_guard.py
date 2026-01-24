import unittest
import shutil
import tempfile
import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.security import SecurityAuditor

class TestSecurityGuard(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.auditor = SecurityAuditor(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_ignore_patterns(self):
        ignore_file = self.test_dir / ".secretignore"
        ignore_file.write_text("tests/fixtures/*\n# comment\nconfig.py")

        self.auditor.load_ignore_patterns()
        self.assertIn("tests/fixtures/*", self.auditor.ignore_patterns)
        self.assertIn("config.py", self.auditor.ignore_patterns)
        self.assertNotIn("# comment", self.auditor.ignore_patterns)

    def test_is_ignored(self):
        self.auditor.ignore_patterns.add("tests/*.json")
        self.auditor.ignore_patterns.add("secret.key")

        # Matches
        self.assertTrue(self.auditor._is_ignored(self.test_dir / "tests/data.json"))
        self.assertTrue(self.auditor._is_ignored(self.test_dir / "secret.key"))

        # No match
        self.assertFalse(self.auditor._is_ignored(self.test_dir / "src/main.py"))
        self.assertFalse(self.auditor._is_ignored(self.test_dir / "tests/script.py"))

    def test_add_ignore_pattern(self):
        self.auditor.add_ignore_pattern("new_secret.txt")
        self.assertIn("new_secret.txt", self.auditor.ignore_patterns)

        ignore_file = self.test_dir / ".secretignore"
        self.assertTrue(ignore_file.exists())
        self.assertIn("new_secret.txt", ignore_file.read_text())

    @patch("shared.security.SecurityAuditor.run_all")
    def test_security_scan_with_ignore(self, mock_run_all):
        # Integration-like test for the scanning logic
        # Create a file that looks like a secret
        secret_file = self.test_dir / "bad_secret.py"
        secret_file.write_text("key = 'AKIAIOSFODNN7EXAMPLE'")

        # Create ignore file
        ignore_file = self.test_dir / ".secretignore"
        ignore_file.write_text("bad_secret.py")

        # Re-init auditor to load patterns
        auditor = SecurityAuditor(self.test_dir)

        # Run scan secrets directly
        findings = auditor.scan_secrets()
        self.assertEqual(len(findings), 0)

        # Remove ignore and scan again
        ignore_file.unlink()
        auditor = SecurityAuditor(self.test_dir) # reload
        findings = auditor.scan_secrets()
        self.assertEqual(len(findings), 1)

if __name__ == "__main__":
    unittest.main()
