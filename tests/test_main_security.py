import unittest
from unittest.mock import patch, MagicMock
import sys
import subprocess
from pathlib import Path
import os
import shutil

# We can run main.py via subprocess to test the full CLI flow
# OR we can import main and test functions, but main.py has global code.
# The memory suggests using subprocess.run([sys.executable, 'main.py', ...])

class TestMainSecurityCLI(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("temp_test_cli_security")
        self.project_dir.mkdir(exist_ok=True)
        # Create a dummy file
        (self.project_dir / "test.py").write_text("print('hello')")

    def tearDown(self):
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    def test_security_help(self):
        cmd = [sys.executable, "main.py", "security", "--help"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("--scan-type", result.stdout)

    def test_security_scan_bandit_mock(self):
        # Since we can't easily mock imports inside the subprocess,
        # we will rely on the fact that run_security calls SecurityAuditor.
        # But for integration, we might want to let it run if dependencies are there.
        # Bandit is installed.

        # This test might be slow or flaky if we actually run bandit.
        # But 'test.py' with print('hello') should be clean for bandit (low severity).

        cmd = [sys.executable, "main.py", "security", "-p", str(self.project_dir), "--scan-type", "bandit"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # It should exit 0 as no issues
        # Note: If bandit fails to run (e.g. not found), it prints error but might exit 0 or 1 depending on our logic.
        # Our logic: if "error" in bandit data, we print it. Exit code depends on has_issues.

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        self.assertIn("Bandit Static Analysis", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_security_scan_secrets_mock(self):
        # Create a file with a secret
        (self.project_dir / "secrets.txt").write_text("aws_key = 'AKIA1234567890ABCDEF'")

        cmd = [sys.executable, "main.py", "security", "-p", str(self.project_dir), "--scan-type", "secrets"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        self.assertIn("Found 1 potential secret(s)", result.stdout)
        self.assertIn("AWS Access Key", result.stdout)
        self.assertEqual(result.returncode, 1) # Should fail by default

    def test_security_scan_secrets_no_fail(self):
        # Create a file with a secret
        (self.project_dir / "secrets.txt").write_text("aws_key = 'AKIA1234567890ABCDEF'")

        cmd = [sys.executable, "main.py", "security", "-p", str(self.project_dir), "--scan-type", "secrets", "--no-fail"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        self.assertIn("Found 1 potential secret(s)", result.stdout)
        self.assertEqual(result.returncode, 0) # Should pass due to --no-fail

if __name__ == "__main__":
    unittest.main()
