"""
Tests for Shared Utilities -> Restricted Paths
============================================
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from shared.utils import execute_read_block, execute_write_block, execute_bash_block, is_restricted_path, RESTRICTED_PATHS

class TestUtilsRestrictedPaths(unittest.IsolatedAsyncioTestCase):

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

    async def test_bash_block_restricted(self):
        # Try cat .env
        result = await execute_bash_block("cat .env", self.project_dir)
        self.assertIn("Error: Access denied", result)
        self.assertIn("restricted path", result)

        # Try rm .git
        result = await execute_bash_block("rm -rf .git", self.project_dir)
        self.assertIn("Error: Access denied", result)

        # Try allowed command
        result = await execute_bash_block("echo hello", self.project_dir)
        self.assertEqual(result.strip(), "hello")

        # Try ls -la (ensure flags don't trigger false positives)
        result = await execute_bash_block("ls -la", self.project_dir)
        self.assertNotIn("Error: Access denied", result)

    async def test_api_collections_restricted(self):
        # Create dummy collection file
        (self.project_dir / ".agent_api_collections.json").write_text("{}")

        # Try to read it
        result = execute_read_block(".agent_api_collections.json", self.project_dir)
        self.assertIn("Error: Access denied", result)
        self.assertIn("restricted path", result)

        # Try to cat it
        result = await execute_bash_block("cat .agent_api_collections.json", self.project_dir)
        self.assertIn("Error: Access denied", result)
        self.assertIn("restricted path", result)

if __name__ == "__main__":
    unittest.main()
