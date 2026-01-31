import unittest
import os
import shutil
import tempfile
import time
from pathlib import Path
from shared.utils import has_recent_activity


class TestUtilsPerformance(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_nested_directory_traversal(self):
        """Verify detection of recent activity in a deeply nested directory."""
        # Create a deep structure
        current_dir = self.test_dir
        for i in range(10):
            current_dir = current_dir / f"dir_{i}"
            current_dir.mkdir()

        # Create a file at the bottom
        target_file = current_dir / "target.txt"
        target_file.touch()

        # Should detect recent activity
        self.assertTrue(has_recent_activity(self.test_dir, seconds=10))

        # Make it old
        os.utime(target_file, (time.time() - 100, time.time() - 100))

        # Should not detect recent activity
        self.assertFalse(has_recent_activity(self.test_dir, seconds=10))

    def test_ignore_patterns_regex(self):
        """Verify that files matching ignore patterns are correctly ignored using regex optimization."""
        # Create a file that should be ignored
        ignored_file = self.test_dir / "ignore_me.log"
        ignored_file.touch()

        # Without ignore patterns, should be true
        self.assertTrue(has_recent_activity(self.test_dir, seconds=10))

        # With ignore patterns, should be false
        self.assertFalse(has_recent_activity(self.test_dir, seconds=10, ignore_patterns=["*.log"]))

        # Create a file that should NOT be ignored
        ok_file = self.test_dir / "ok.txt"
        ok_file.touch()

        # Should be true now
        self.assertTrue(has_recent_activity(self.test_dir, seconds=10, ignore_patterns=["*.log"]))

    def test_ignore_patterns_complex(self):
        """Verify multiple ignore patterns."""
        (self.test_dir / "temp.tmp").touch()
        (self.test_dir / "temp.log").touch()

        self.assertFalse(has_recent_activity(self.test_dir, seconds=10, ignore_patterns=["*.tmp", "*.log"]))

        (self.test_dir / "real.py").touch()
        self.assertTrue(has_recent_activity(self.test_dir, seconds=10, ignore_patterns=["*.tmp", "*.log"]))

    def test_empty_directory(self):
        """Verify behavior with empty directory."""
        self.assertFalse(has_recent_activity(self.test_dir, seconds=10))

    def test_ignored_directories_skipped(self):
        """Verify that IGNORED_DIRS are skipped."""
        # Create a hidden directory that is in IGNORED_DIRS (e.g. .git)
        git_dir = self.test_dir / ".git"
        git_dir.mkdir()
        (git_dir / "recent_change").touch()

        # Should be ignored because .git is in IGNORED_DIRS in shared/utils.py
        self.assertFalse(has_recent_activity(self.test_dir, seconds=10))


if __name__ == "__main__":
    unittest.main()
