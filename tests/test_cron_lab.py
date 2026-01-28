import unittest
import sys
from unittest.mock import MagicMock, patch
from datetime import datetime

# Ensure shared module is in path
sys.path.append(".")
from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_validate_valid(self):
        self.assertTrue(self.manager.validate("*/5 * * * *"))
        self.assertTrue(self.manager.validate("0 0 1 1 *"))

    def test_validate_invalid(self):
        self.assertFalse(self.manager.validate("invalid"))
        self.assertFalse(self.manager.validate("60 * * * *")) # Minute 60 is invalid

    def test_describe(self):
        # Heuristic test
        desc = self.manager.describe("*/5 * * * *")
        self.assertIn("Every 5 minutes", desc)

        desc = self.manager.describe("0 0 1 1 *")
        self.assertIn("At minute 0", desc)
        self.assertIn("on day-of-month 1", desc)

    def test_get_next_occurrences(self):
        fixed_now = datetime(2023, 1, 1, 12, 0, 0)
        occurrences = self.manager.get_next_occurrences("*/15 * * * *", count=3, start_time=fixed_now)

        self.assertEqual(len(occurrences), 3)
        self.assertEqual(occurrences[0], datetime(2023, 1, 1, 12, 15))
        self.assertEqual(occurrences[1], datetime(2023, 1, 1, 12, 30))
        self.assertEqual(occurrences[2], datetime(2023, 1, 1, 12, 45))

if __name__ == '__main__':
    unittest.main()
