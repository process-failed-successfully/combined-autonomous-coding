"""
Tests for Shared Utilities -> Security Tests
============================================
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from shared.utils import execute_read_block, execute_write_block

class TestUtilsSecurity(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Create a file outside the project directory
        self.outside_dir = tempfile.mkdtemp()
        self.secret_file = Path(self.outside_dir) / "secret.txt"
        with open(self.secret_file, "w") as f:
            f.write("SECRET_CONTENT")

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.outside_dir)

    def test_read_block_path_traversal(self):
        """Test that execute_read_block prevents reading files outside project_dir."""

        # Try to read the file using relative path traversal
        rel_path = f"../{os.path.basename(self.outside_dir)}/secret.txt"

        # Ensure we are actually constructing a path that points to the secret file
        resolved = (self.project_dir / rel_path).resolve()
        self.assertEqual(resolved, self.secret_file)

        result = execute_read_block(rel_path, self.project_dir)

        self.assertIn("Error: Access denied", result)
        self.assertNotIn("SECRET_CONTENT", result)

    def test_write_block_path_traversal(self):
        """Test that execute_write_block prevents writing files outside project_dir."""

        rel_path = f"../{os.path.basename(self.outside_dir)}/hacked.txt"
        content = "hacked"

        result = execute_write_block(rel_path, content, self.project_dir)

        self.assertIn("Error: Access denied", result)

        target_file = Path(self.outside_dir) / "hacked.txt"
        self.assertFalse(target_file.exists())

    def test_read_block_valid_file(self):
        """Test that execute_read_block works for valid files."""
        filename = "valid.txt"
        with open(self.project_dir / filename, "w") as f:
            f.write("valid content")

        result = execute_read_block(filename, self.project_dir)
        self.assertIn("valid content", result)

    def test_write_block_valid_file(self):
        """Test that execute_write_block works for valid files."""
        filename = "new_file.txt"
        content = "new content"

        result = execute_write_block(filename, content, self.project_dir)
        self.assertIn("Successfully wrote", result)

        with open(self.project_dir / filename, "r") as f:
            self.assertEqual(f.read(), content)

    def test_is_safe_git_ref(self):
        """Test the is_safe_git_ref validator."""
        from shared.utils import is_safe_git_ref

        # Valid refs
        self.assertTrue(is_safe_git_ref("main"))
        self.assertTrue(is_safe_git_ref("feature/branch-name"))
        self.assertTrue(is_safe_git_ref("v1.0.0"))
        self.assertTrue(is_safe_git_ref("HEAD"))
        self.assertTrue(is_safe_git_ref("HEAD~1"))
        self.assertTrue(is_safe_git_ref("HEAD^"))
        self.assertTrue(is_safe_git_ref("origin/main"))
        self.assertTrue(is_safe_git_ref("a"*40)) # Commit hash

        # Invalid refs
        self.assertFalse(is_safe_git_ref("-flag"))
        self.assertFalse(is_safe_git_ref("--option"))
        self.assertFalse(is_safe_git_ref("branch with spaces"))
        self.assertFalse(is_safe_git_ref("branch;command"))
        self.assertFalse(is_safe_git_ref("branch|command"))
        self.assertFalse(is_safe_git_ref("branch&command"))
        self.assertFalse(is_safe_git_ref("branch>file"))
        self.assertFalse(is_safe_git_ref(""))

if __name__ == "__main__":
    unittest.main()
