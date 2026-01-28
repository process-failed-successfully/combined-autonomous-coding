import unittest
from datetime import datetime
from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def test_validate_valid(self):
        self.assertTrue(CronLabManager.validate("* * * * *"))
        self.assertTrue(CronLabManager.validate("*/5 * * * *"))
        self.assertTrue(CronLabManager.validate("0 12 * * MON"))

    def test_validate_invalid(self):
        self.assertFalse(CronLabManager.validate("invalid"))
        self.assertFalse(CronLabManager.validate("* * * *")) # Missing field

    def test_get_next_runs(self):
        # Every minute
        start = datetime(2023, 1, 1, 12, 0, 0)
        runs = CronLabManager.get_next_runs("* * * * *", count=2, start_time=start)
        self.assertEqual(len(runs), 2)
        self.assertEqual(runs[0], datetime(2023, 1, 1, 12, 1, 0))
        self.assertEqual(runs[1], datetime(2023, 1, 1, 12, 2, 0))

    def test_describe(self):
        self.assertEqual(CronLabManager.describe("* * * * *"), "Every minute")
        self.assertIn("Every 5 minutes", CronLabManager.describe("*/5 * * * *"))

if __name__ == '__main__':
    unittest.main()
