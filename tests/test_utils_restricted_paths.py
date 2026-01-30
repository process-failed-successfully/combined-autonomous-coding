"""
Tests for Shared Utilities -> Restricted Paths
============================================
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from shared.utils import execute_read_block, execute_write_block, is_restricted_path, RESTRICTED_PATHS

class TestUtilsRestrictedPaths(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        (self.project_dir / ".git").mkdir()
        (self.project_dir / ".git" / "config").write_text("config")
        (self.project_dir / ".env").write_text("SECRET=123")
        (self.project_dir / "src").mkdir()
        (self.project_dir / "src" / ".env.local").write_text("SECRET=456")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_is_restricted_path(self):
        # Restricted
        self.assertTrue(is_restricted_path(self.project_dir / ".git/config", self.project_dir))
        self.assertTrue(is_restricted_path(self.project_dir / ".env", self.project_dir))
        self.assertTrue(is_restricted_path(self.project_dir / "src/.env.local", self.project_dir))
        self.assertTrue(is_restricted_path(self.project_dir / "src/.git/HEAD", self.project_dir))

        # Not restricted
        self.assertFalse(is_restricted_path(self.project_dir / "main.py", self.project_dir))
        self.assertFalse(is_restricted_path(self.project_dir / "src/utils.py", self.project_dir))
        self.assertFalse(is_restricted_path(self.project_dir / "git_utils.py", self.project_dir)) # "git" in name but not .git

    def test_write_block_restricted(self):
        # Try writing to .git
        result = execute_write_block(".git/hooks/evil.sh", "evil", self.project_dir)
        self.assertIn("Error: Access denied", result)
        self.assertIn("restricted path", result)
        self.assertFalse((self.project_dir / ".git/hooks/evil.sh").exists())

        # Try writing to .env
        result = execute_write_block(".env", "SECRET=HACKED", self.project_dir)
        self.assertIn("Error: Access denied", result)

    def test_read_block_restricted(self):
        # Try reading .git/config
        result = execute_read_block(".git/config", self.project_dir)
        self.assertIn("Error: Access denied", result)
        self.assertIn("restricted path", result)

        # Try reading .env
        result = execute_read_block(".env", self.project_dir)
        self.assertIn("Error: Access denied", result)

if __name__ == "__main__":
    unittest.main()
