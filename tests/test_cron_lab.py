import unittest
from datetime import datetime, timedelta
from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_validate(self):
        self.assertTrue(self.manager.validate("*/15 * * * *"))
        self.assertTrue(self.manager.validate("0 9 * * 1-5"))
        self.assertFalse(self.manager.validate("invalid"))
        self.assertFalse(self.manager.validate("* * * *")) # Too short

    def test_describe(self):
        self.assertEqual(self.manager.describe("* * * * *"), "Every minute every day")
        self.assertIn("At 09:00", self.manager.describe("0 9 * * *"))
        self.assertEqual(self.manager.describe("invalid"), "Invalid cron expression")

    def test_get_next_occurrences(self):
        # Specific start time: 2024-01-01 10:00:00
        start = datetime(2024, 1, 1, 10, 0, 0)

        # Every 15 minutes: 10:15, 10:30
        expr = "*/15 * * * *"
        occurrences = self.manager.get_next_occurrences(expr, 2, start_time=start)

        self.assertEqual(len(occurrences), 2)
        self.assertEqual(occurrences[0], datetime(2024, 1, 1, 10, 15, 0))
        self.assertEqual(occurrences[1], datetime(2024, 1, 1, 10, 30, 0))

if __name__ == '__main__':
    unittest.main()
