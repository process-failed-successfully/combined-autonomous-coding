
import unittest
import subprocess
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Adjust the path to import from the root of the project
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestMainAnalyticsComplexity(unittest.TestCase):

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

    def test_analytics_complexity(self):
        """Test 'analytics complexity' command."""
        # Create a Python file with known complexity
        code = """
def complex_func(x):
    if x > 0:
        if x > 10:
            return 1
        else:
            return 2
    elif x < 0:
        return -1
    else:
        return 0
"""
        # Complexity: 1 (base) + 1 (if >0) + 1 (if >10) + 1 (elif) = 4

        (self.project_dir / "complex.py").write_text(code)

        # Create a simple file
        (self.project_dir / "simple.py").write_text("def simple(): pass")

        result = self.run_cli(["analytics", "complexity"])

        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        self.assertEqual(result.returncode, 0)
        self.assertIn("Code Complexity Analysis", result.stdout)
        self.assertIn("complex_func", result.stdout)
        self.assertIn("complex.py", result.stdout)
        # Check if the complexity value is present (should be 4)
        self.assertRegex(result.stdout, r"4\s+\|\s+complex\.py")
        self.assertIn("simple", result.stdout)

    def test_analytics_complexity_no_python_files(self):
        """Test with no Python files."""
        (self.project_dir / "README.md").write_text("# Hello")

        result = self.run_cli(["analytics", "complexity"])

        if result.returncode != 0:
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")

        self.assertEqual(result.returncode, 0)
        self.assertIn("No Python functions found", result.stdout)

if __name__ == '__main__':
    unittest.main()
