import unittest
import shutil
import subprocess  # nosec B404
import tempfile
from pathlib import Path
from shared.security import SecurityAuditor

class TestSecurityHistory(unittest.TestCase):
    def setUp(self):
        self.test_dir_obj = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.test_dir_obj.name)

        # Init git repo
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603

        self.auditor = SecurityAuditor(self.test_dir)

    def tearDown(self):
        self.test_dir_obj.cleanup()

    def test_scan_git_history_finds_secret(self):
        # 1. Commit a secret
        secret_file = self.test_dir / "secret.py"
        secret_content = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
        secret_file.write_text(secret_content)

        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603
        subprocess.run(["git", "commit", "-m", "Add secret"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603

        # 2. Remove the secret
        secret_file.write_text("AWS_KEY = 'REDACTED'")

        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603
        subprocess.run(["git", "commit", "-m", "Remove secret"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603

        # 3. Scan history
        findings = self.auditor.scan_git_history(depth=10)

        # 4. Verify
        # Should find 1 secret
        self.assertTrue(len(findings) >= 1, "Should find at least one secret in history")

        found = False
        for f in findings:
            if "AWS Access Key" in f["description"]:
                found = True
                self.assertEqual(f["type"], "secret_history")
                self.assertEqual(f["file"], "secret.py")
                self.assertIn("AKIA***", f["snippet"])
                self.assertIsNotNone(f["commit"])
                self.assertIsNotNone(f["author"])
                self.assertIsNotNone(f["date"])

        self.assertTrue(found, "Did not find the specific AWS key finding")

    def test_scan_git_history_ignores_safe_commits(self):
        # 1. Commit safe code
        safe_file = self.test_dir / "safe.py"
        safe_file.write_text("print('Hello World')")

        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603
        subprocess.run(["git", "commit", "-m", "Safe commit"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603

        # 2. Scan history
        findings = self.auditor.scan_git_history(depth=10)

        # 3. Verify
        self.assertEqual(len(findings), 0, "Should not find any secrets")

    def test_scan_git_history_path_with_spaces(self):
        # 1. Commit a secret in a file with spaces
        secret_file = self.test_dir / "my secret file.py"
        secret_content = "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'"
        secret_file.write_text(secret_content)

        subprocess.run(["git", "add", "."], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603
        subprocess.run(["git", "commit", "-m", "Add secret in file with spaces"], cwd=self.test_dir, check=True, capture_output=True)  # nosec B603

        # 2. Scan history
        findings = self.auditor.scan_git_history(depth=10)

        # 3. Verify
        found = False
        for f in findings:
            if "AWS Access Key" in f["description"]:
                found = True
                self.assertEqual(f["file"], "my secret file.py")

        self.assertTrue(found, "Did not handle file with spaces correctly")

if __name__ == "__main__":
    unittest.main()
