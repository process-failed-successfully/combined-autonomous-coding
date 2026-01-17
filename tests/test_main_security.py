"""
Integration Tests for 'security' command in main.py
===================================================
"""

import sys
import shutil
import tempfile
import subprocess
import unittest
import os
from pathlib import Path

class TestMainSecurity(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.main_script = Path("main.py").resolve()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_command(self, args):
        """Helper to run the main script with arguments."""
        cmd = [sys.executable, str(self.main_script)] + args
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd())
        return subprocess.run(
            cmd,
            cwd=self.test_dir,
            capture_output=True,
            text=True,
            env=env
        )

    def test_security_clean(self):
        """Test security command on a clean project."""
        # Create a safe file
        (self.project_dir / "safe.py").write_text("print('Hello World')")

        result = self.run_command(["security", "-p", str(self.project_dir)])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Running Security Audit", result.stdout)
        self.assertIn("No security issues found", result.stdout)

    def test_security_with_issues(self):
        """Test security command on a project with issues."""
        # Create a file with a secret
        (self.project_dir / "config.py").write_text("aws_key = 'AKIA1234567890123456'")

        # Create a file with a bandit issue (exec)
        (self.project_dir / "unsafe.py").write_text("exec('print(1)')")

        result = self.run_command(["security", "-p", str(self.project_dir)])

        self.assertNotEqual(result.returncode, 0) # Should fail
        self.assertIn("Running Security Audit", result.stdout)
        self.assertIn("Found", result.stdout)
        self.assertIn("potential security issue(s)", result.stdout)

        # Check specific findings
        self.assertIn("AWS Access Key", result.stdout) # From secret scan
        self.assertIn("Use of exec detected", result.stdout) # From bandit

    def test_security_no_fail(self):
        """Test security command with --no-fail flag."""
        # Create a file with a secret
        (self.project_dir / "config.py").write_text("aws_key = 'AKIA1234567890123456'")

        result = self.run_command(["security", "-p", str(self.project_dir), "--no-fail"])

        self.assertEqual(result.returncode, 0) # Should pass despite issues
        self.assertIn("Found", result.stdout)
        self.assertIn("potential security issue(s)", result.stdout)

    def test_scan_type_secrets_only(self):
        """Test running only secret scanning."""
        # Create a file with a secret and a bandit issue
        (self.project_dir / "config.py").write_text("aws_key = 'AKIA1234567890123456'")
        (self.project_dir / "unsafe.py").write_text("exec('print(1)')")

        result = self.run_command(["security", "-p", str(self.project_dir), "--scan-type", "secrets"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("AWS Access Key", result.stdout)
        self.assertNotIn("Use of exec detected", result.stdout) # Should not run bandit

    def test_scan_type_bandit_only(self):
        """Test running only bandit scanning."""
        # Create a file with a secret and a bandit issue
        (self.project_dir / "config.py").write_text("aws_key = 'AKIA1234567890123456'")
        (self.project_dir / "unsafe.py").write_text("exec('print(1)')")

        result = self.run_command(["security", "-p", str(self.project_dir), "--scan-type", "bandit"])

        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("AWS Access Key", result.stdout) # Should not find secret
        self.assertIn("Use of exec detected", result.stdout)

if __name__ == "__main__":
    unittest.main()
