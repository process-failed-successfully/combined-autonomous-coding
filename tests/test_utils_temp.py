import unittest
import os
import shutil
import tempfile
from pathlib import Path
import time
from shared.utils import has_recent_activity

class TestHasRecentActivityTemp(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_has_recent_activity_ignore_patterns_bug(self):
        # Create a file that should be ignored
        ignored_file = self.test_dir / "activity.log"
        ignored_file.touch()

        # The function should return False, but it's returning True
        self.assertFalse(
            has_recent_activity(
                self.test_dir, seconds=10, ignore_patterns=["*.log"]
            ),
            "Failed to ignore the log file."
        )

        # Create a non-ignored file to ensure the function works otherwise
        non_ignored_file = self.test_dir / "activity.py"
        non_ignored_file.touch()

        self.assertTrue(
            has_recent_activity(
                self.test_dir, seconds=10, ignore_patterns=["*.log"]
            ),
            "Failed to detect the non-ignored file."
        )

if __name__ == "__main__":
    unittest.main()
