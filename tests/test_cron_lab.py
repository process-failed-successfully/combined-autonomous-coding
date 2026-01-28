import unittest
from datetime import datetime, timedelta
from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_validate_valid(self):
        self.assertTrue(self.manager.validate("* * * * *"))
        self.assertTrue(self.manager.validate("0 5 * * 1"))
        self.assertTrue(self.manager.validate("*/15 * * * *"))

    def test_validate_invalid(self):
        self.assertFalse(self.manager.validate("invalid"))
        self.assertFalse(self.manager.validate("* * * *")) # Too few
        self.assertFalse(self.manager.validate("60 * * * *")) # Invalid minute

    def test_explain(self):
        # Basic check that it returns a string and handles invalid input
        self.assertEqual(self.manager.explain("invalid"), "Invalid cron expression.")
        self.assertIsInstance(self.manager.explain("* * * * *"), str)
        self.assertIn("Every minute", self.manager.explain("* * * * *"))

    def test_get_next_runs(self):
        runs = self.manager.get_next_runs("* * * * *", count=3)
        self.assertEqual(len(runs), 3)
        self.assertIsInstance(runs[0], datetime)

        # Check that runs are increasing
        self.assertLess(runs[0], runs[1])
        self.assertLess(runs[1], runs[2])

    def test_generate_from_text(self):
        self.assertEqual(self.manager.generate_from_text("every minute"), "* * * * *")
        self.assertEqual(self.manager.generate_from_text("daily"), "0 0 * * *")
        self.assertEqual(self.manager.generate_from_text("unknown text"), "")

if __name__ == '__main__':
    unittest.main()
