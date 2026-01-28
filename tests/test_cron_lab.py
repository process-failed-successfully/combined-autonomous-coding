import unittest
from datetime import datetime
from shared.cron_lab import CronLabManager

class TestCronLab(unittest.TestCase):
    def test_validation(self):
        manager = CronLabManager()
        valid, msg = manager.validate("*/5 * * * *")
        self.assertTrue(valid)

        valid, msg = manager.validate("invalid")
        self.assertFalse(valid)

    def test_next_occurrences(self):
        manager = CronLabManager()
        # Mock start time 2023-01-01 00:00:00
        start = datetime(2023, 1, 1, 0, 0, 0)

        dates = manager.get_next_occurrences("*/15 * * * *", start_time=start, count=3)
        self.assertEqual(len(dates), 3)
        self.assertEqual(dates[0], datetime(2023, 1, 1, 0, 15))
        self.assertEqual(dates[1], datetime(2023, 1, 1, 0, 30))
        self.assertEqual(dates[2], datetime(2023, 1, 1, 0, 45))

if __name__ == "__main__":
    unittest.main()
