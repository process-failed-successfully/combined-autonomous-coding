import unittest
from shared.cron_lab import CronLabManager

class TestCronLab(unittest.TestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_validate(self):
        self.assertTrue(self.manager.validate("* * * * *"))
        self.assertTrue(self.manager.validate("*/5 * * * *"))
        self.assertFalse(self.manager.validate("invalid"))
        self.assertFalse(self.manager.validate("* * * *")) # Too short

    def test_describe_preset(self):
        self.assertEqual(self.manager.describe("* * * * *"), "Every minute")
        self.assertEqual(self.manager.describe("0 0 * * *"), "Every day at midnight")

    def test_describe_dynamic(self):
        self.assertEqual(self.manager.describe("*/5 * * * *"), "Every 5 minutes")
        self.assertEqual(self.manager.describe("15 * * * *"), "Every hour at minute 15")

    def test_next_occurrences(self):
        next_runs = self.manager.get_next_occurrences("0 0 * * *", count=3)
        self.assertEqual(len(next_runs), 3)
        # We can't easily check exact timestamps without mocking datetime, but we can check format
        # and ascending order
        from datetime import datetime
        dts = [datetime.fromisoformat(x) for x in next_runs]
        self.assertTrue(dts[0] < dts[1] < dts[2])

if __name__ == "__main__":
    unittest.main()
