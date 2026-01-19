import unittest
import subprocess
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Adjust the path to import from the root of the project
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestMainDuplication(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.main_path = Path(__file__).parent.parent / "main.py"

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def run_cli(self, args):
        """Helper to run the CLI."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent)
        result = subprocess.run(
            [sys.executable, str(self.main_path)] + args,
            cwd=self.project_dir,
            capture_output=True,
            text=True,
            env=env
        )
        return result

    def test_duplication_command(self):
        """Test 'duplication' command with duplicates."""
        # Create unique content but duplicated across two files
        lines = [f"var_{i} = {i}" for i in range(50)]
        content = "\n".join(lines)

        (self.project_dir / "file1.py").write_text(content)
        (self.project_dir / "file2.py").write_text(content)

        result = self.run_cli(["duplication", "--min-tokens", "50", "-p", str(self.project_dir)])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Code Duplication Detector", result.stdout)
        self.assertIn("Found", result.stdout)
        self.assertIn("duplicate blocks", result.stdout)
        self.assertIn("file1.py", result.stdout)
        self.assertIn("file2.py", result.stdout)

    def test_duplication_no_duplicates(self):
        """Test 'duplication' command with no duplicates."""
        (self.project_dir / "file1.py").write_text("a = 1")
        (self.project_dir / "file2.py").write_text("b = 2")

        result = self.run_cli(["duplication", "--min-tokens", "10", "-p", str(self.project_dir)])

        self.assertEqual(result.returncode, 0)
        self.assertIn("Code Duplication Detector", result.stdout)
        self.assertIn("No duplicates found", result.stdout)

    def test_duplication_ignore(self):
        """Test 'duplication' command with ignore."""
        lines = [f"var_{i} = {i}" for i in range(50)]
        content = "\n".join(lines)

        (self.project_dir / "file1.py").write_text(content)
        (self.project_dir / "ignored.py").write_text(content)

        # First run without ignore
        result1 = self.run_cli(["duplication", "--min-tokens", "50", "-p", str(self.project_dir)])
        self.assertIn("Found", result1.stdout)

        # Run with ignore
        result2 = self.run_cli(["duplication", "--min-tokens", "50", "--ignore", "ignored.py", "-p", str(self.project_dir)])
        self.assertIn("No duplicates found", result2.stdout)

if __name__ == '__main__':
    unittest.main()
