import sys
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

class TestMainSecurity(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        # Use absolute path to main.py
        self.main_py = Path("main.py").resolve()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_security_command_detects_issues(self):
        # Create a file with a secret (AWS Key)
        # We rely on the secret scanner here as it doesn't depend on external tools like bandit
        # (though bandit might also be installed)
        (self.test_dir / "vulnerable.py").write_text("aws_key = 'AKIA1234567890123456'")

        # Run command
        result = subprocess.run(
            [sys.executable, str(self.main_py), "security", "--project-dir", str(self.test_dir)],
            capture_output=True,
            text=True
        )

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        self.assertIn("Security Audit", result.stdout)
        self.assertIn("Secrets Detected", result.stdout)
        self.assertIn("AWS Access Key", result.stdout)

        # Should fail (exit 1) because issues were found
        self.assertEqual(result.returncode, 1)

    def test_security_command_no_fail(self):
        (self.test_dir / "vulnerable.py").write_text("aws_key = 'AKIA1234567890123456'")

        result = subprocess.run(
            [sys.executable, str(self.main_py), "security", "--project-dir", str(self.test_dir), "--no-fail"],
            capture_output=True,
            text=True
        )

        self.assertIn("Secrets Detected", result.stdout)
        # Should pass (exit 0) because of --no-fail
        self.assertEqual(result.returncode, 0)

if __name__ == '__main__':
    unittest.main()
