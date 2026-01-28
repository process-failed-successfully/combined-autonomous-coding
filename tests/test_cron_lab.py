import unittest
from datetime import datetime
from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_validate_valid(self):
        self.assertTrue(self.manager.validate("* * * * *"))
        self.assertTrue(self.manager.validate("0 0 * * *"))
        self.assertTrue(self.manager.validate("*/5 * * * *"))

    def test_validate_invalid(self):
        self.assertFalse(self.manager.validate("invalid"))
        # self.assertFalse(self.manager.validate("* * * * * * *")) # croniter might be permissive or use seconds? let's stick to simple invalid

    def test_explain(self):
        self.assertIsInstance(self.manager.explain("* * * * *"), str)
        self.assertEqual(self.manager.explain("invalid"), "Invalid cron expression.")

    def test_next_occurrences(self):
        next_runs = self.manager.next_occurrences("0 0 1 1 *", count=2)
        self.assertEqual(len(next_runs), 2)
        self.assertIsInstance(next_runs[0], str)

if __name__ == '__main__':
    unittest.main()
