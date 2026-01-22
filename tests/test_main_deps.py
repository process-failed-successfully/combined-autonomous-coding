
import unittest
import subprocess
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Adjust the path to import from the root of the project
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMainDeps(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.main_path = Path(__file__).parent.parent / "main.py"

        # Create dummy dependency files
        (self.project_dir / "requirements.txt").write_text("flask==2.0.1\n")
        (self.project_dir / "package.json").write_text('{"dependencies": {"express": "^4.17.1"}}')

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

    def test_deps_default(self):
        """Test 'deps' command with default output (tree)."""
        result = self.run_cli(["deps"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("📦 Python", result.stdout)
        self.assertIn("flask ==2.0.1", result.stdout)
        self.assertIn("📦 Node", result.stdout)
        self.assertIn("express ^4.17.1", result.stdout)

    def test_deps_mermaid(self):
        """Test 'deps' command with mermaid output."""
        result = self.run_cli(["deps", "--format", "mermaid"])
        self.assertEqual(result.returncode, 0)
        self.assertIn("graph TD", result.stdout)
        self.assertIn("root --> lang_python[Python]", result.stdout)
        self.assertIn("--> dep_node_0_express", result.stdout)

    def test_deps_json(self):
        """Test 'deps' command with json output."""
        result = self.run_cli(["deps", "--format", "json"])
        self.assertEqual(result.returncode, 0)
        self.assertIn('"source": "requirements.txt"', result.stdout)
        self.assertIn('"flask"', result.stdout)
        self.assertIn('"express"', result.stdout)


if __name__ == '__main__':
    unittest.main()
