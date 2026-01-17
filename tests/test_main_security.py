import unittest
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path
import os

class TestMainSecurityCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.main_py = Path(__file__).parent.parent / "main.py"

        # Create a dummy python file with a security issue (assert usage)
        (self.test_dir / "bad_code.py").write_text("def foo():\n    assert True\n")

        # Create a dummy python file with a secret
        # Pattern AKIA... (20 chars)
        (self.test_dir / "secrets.py").write_text("key = 'AKIA0000000000000000'\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_security_command_scan_all(self):
        # Run security command
        cmd = [
            sys.executable,
            str(self.main_py),
            "security",
            "--project-dir", str(self.test_dir),
            "--no-fail" # Don't exit with error so we can check output easily
        ]

        # We need to make sure PYTHONPATH includes the repo root so main.py can find shared/
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.main_py.parent)

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode != 0:
            print("STDERR:", result.stderr)
            print("STDOUT:", result.stdout)

        self.assertEqual(result.returncode, 0)
        self.assertIn("Running Security Scan", result.stdout)
        self.assertIn("B101", result.stdout) # Assert used
        self.assertIn("SECRET-SCAN", result.stdout) # Secret found

    def test_security_command_scan_static_only(self):
        cmd = [
            sys.executable,
            str(self.main_py),
            "security",
            "--project-dir", str(self.test_dir),
            "--scan-type", "static",
            "--no-fail"
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.main_py.parent)

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        self.assertIn("B101", result.stdout)
        self.assertNotIn("SECRET-SCAN", result.stdout)

    def test_security_command_fail_exit_code(self):
        # Should fail by default if issues found
        cmd = [
            sys.executable,
            str(self.main_py),
            "security",
            "--project-dir", str(self.test_dir)
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.main_py.parent)

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        self.assertNotEqual(result.returncode, 0)

if __name__ == "__main__":
    unittest.main()
