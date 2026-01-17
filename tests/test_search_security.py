
"""
Tests for Shared Utilities -> execute_search_block Security
===========================================================
"""

import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
from shared.utils import execute_search_block

class TestSearchSecurity(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Create a file to search in
        (self.project_dir / "target.txt").write_text("This is a line with the secret keyword.\nContext line 1.\nContext line 2.")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    async def test_search_valid(self):
        """Test valid search query."""
        query = "secret keyword"
        output = await execute_search_block(query, self.project_dir)
        self.assertIn("target.txt", output)
        self.assertIn("This is a line with the secret keyword", output)

    async def test_search_leading_hyphen(self):
        """Test that queries starting with a hyphen are treated as patterns, not flags."""
        # Create a file with content starting with a hyphen
        (self.project_dir / "hyphen.txt").write_text("-flag_like_content")

        query = "-flag_like_content"
        output = await execute_search_block(query, self.project_dir)
        self.assertIn("hyphen.txt", output)
        self.assertIn("-flag_like_content", output)

    async def test_search_injection_attempt(self):
        """Test that command injection is prevented."""
        # Attempt to create a file via injection
        # If vulnerable: ' . ; touch hacked.txt ; echo ' would create hacked.txt
        injection_query = "' . ; touch hacked.txt ; echo '"

        output = await execute_search_block(injection_query, self.project_dir)

        # Check that the file was NOT created
        self.assertFalse((self.project_dir / "hacked.txt").exists(), "Command injection succeeded: hacked.txt was created")

        # Output should likely be empty or grep error, but definitely not contain success of touch
        # Since we search for literal string (or regex) containing quotes and semicolons, grep probably just didn't find it.

    async def test_search_regex(self):
        """Test that regex search still works (as arguments are passed to grep)."""
        query = "secret.*keyword"
        output = await execute_search_block(query, self.project_dir)
        self.assertIn("target.txt", output)
        self.assertIn("This is a line with the secret keyword", output)

if __name__ == "__main__":
    unittest.main()
