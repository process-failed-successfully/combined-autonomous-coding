import unittest
from unittest.mock import patch
import subprocess
from pathlib import Path
import tempfile
import shutil
import os

# Make sure the main script can be imported
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import parse_args
from shared.cli_utils import _run_context_show_logic, _run_context_analyze_logic

class TestContextCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

        # Create a mock file structure
        (self.project_dir / "src").mkdir()
        (self.project_dir / "src" / "main.py").write_text("print('hello')") # 14 bytes in some envs
        (self.project_dir / "src" / "utils.py").write_text("def helper(): pass") # 18 bytes
        (self.project_dir / "docs").mkdir()
        (self.project_dir / "docs" / "guide.md").write_text("# Guide") # 7 bytes
        (self.project_dir / "ignored_file.log").write_text("log data") # 8 bytes
        (self.project_dir / "node_modules").mkdir()
        (self.project_dir / "node_modules" / "some_lib.js").write_text("lib code")

        # Initialize a git repo and create a .gitignore
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        (self.project_dir / ".gitignore").write_text("*.log\nnode_modules/\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shutil.which', return_value='git')
    def test_context_show_logic(self, mock_which):
        """Test the logic for `context show` command."""
        output = _run_context_show_logic(self.project_dir)

        # Check for key elements in the output
        self.assertIn("--- Agent Context Analysis: test_project/ ---", output)
        self.assertIn("src/", output)
        self.assertIn("main.py", output)
        self.assertIn("14 B", output)
        self.assertIn("utils.py", output)
        self.assertIn("18 B", output)
        self.assertIn("docs/", output)
        self.assertIn("guide.md", output)
        self.assertIn("7 B", output)
        self.assertIn(".gitignore", output)

        # Ignored files should not be present
        self.assertNotIn("ignored_file.log", output)
        self.assertNotIn("node_modules/", output)
        self.assertNotIn(".git/", output)

        # Check the summary
        self.assertIn("--- Context Summary ---", output)
        self.assertIn("Total Files:      4", output) # .gitignore, main.py, utils.py, guide.md

        total_size = 14 + 18 + 7 + (self.project_dir / ".gitignore").stat().st_size
        self.assertIn(f"Total Size:       {total_size} B", output)


    @patch('shutil.which', return_value='git')
    def test_context_analyze_logic(self, mock_which):
        """Test the logic for `context analyze` command."""
        output = _run_context_analyze_logic(self.project_dir)

        self.assertIn("--- Agent Context Analysis by File Type: test_project/ ---", output)
        self.assertIn("Extension", output)
        self.assertIn("Count", output)
        self.assertIn("Total Size", output)
        self.assertIn("Percentage", output)

        # Check for specific file types
        self.assertIn(".py", output)
        self.assertIn(".md", output)
        self.assertIn("(no extension)", output) # for .gitignore

        # Check stats for .py files (14 + 18 = 32)
        self.assertIn(f" 2 ", output) # Count for .py
        self.assertIn(f" 32 B", output) # Size for .py

        # Check totals
        self.assertIn("TOTAL", output)
        self.assertIn(f" 4 ", output) # Total count


if __name__ == '__main__':
    unittest.main()
