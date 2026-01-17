"""
Tests for Shared Utilities -> Security Tests
============================================
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from shared.utils import execute_read_block, execute_write_block, is_safe_git_ref

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

    def test_git_ref_valid(self):
        valid_refs = [
            "HEAD",
            "main",
            "feature/new-branch",
            "v1.0.0",
            "a1b2c3d",
            "HEAD~1",
            "HEAD^",
            "stash@{0}",
            "origin/main",
            "user_name/branch-name.1",
        ]
        for ref in valid_refs:
            with self.subTest(ref=ref):
                self.assertTrue(is_safe_git_ref(ref), f"Ref '{ref}' should be valid")

    def test_git_ref_invalid(self):
        invalid_refs = [
            "-flag",
            "--option",
            "; rm -rf /",
            "commit; command",
            "| pipe",
            "> redirect",
            "`backtick`",
            "$(command)",
            "",
            None,
            "HEAD:file.txt", # Colon not allowed
        ]
        for ref in invalid_refs:
            with self.subTest(ref=ref):
                self.assertFalse(is_safe_git_ref(ref), f"Ref '{ref}' should be invalid")

if __name__ == "__main__":
    unittest.main()
