import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import datetime
import asyncio

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_validate_valid(self):
        valid, msg = self.manager.validate("*/5 * * * *")
        self.assertTrue(valid)
        self.assertIn("Valid", msg)

    def test_validate_invalid(self):
        valid, msg = self.manager.validate("invalid cron")
        self.assertFalse(valid)
        self.assertIn("Invalid", msg)

    def test_validate_empty(self):
        valid, msg = self.manager.validate("")
        self.assertFalse(valid)
        self.assertIn("empty", msg)

    def test_get_next_occurrences(self):
        # Every minute
        occurrences = self.manager.get_next_occurrences("* * * * *", count=3)
        self.assertEqual(len(occurrences), 3)
        self.assertIsInstance(occurrences[0], datetime.datetime)
        self.assertLess(occurrences[0], occurrences[1])

    def test_get_next_occurrences_invalid(self):
        occurrences = self.manager.get_next_occurrences("invalid")
        self.assertEqual(occurrences, [])

class TestCronLabManagerAsync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = CronLabManager()

    @patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_explain(self, mock_ask):
        async def side_effect(*args, **kwargs):
            print("--- Answer ---\nAt 5 minutes past the hour\n--------------")
            return True

        mock_ask.side_effect = side_effect

        result = await self.manager.explain("5 * * * *")
        self.assertEqual(result, "At 5 minutes past the hour")

    @patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_generate(self, mock_ask):
        async def side_effect(*args, **kwargs):
            print("--- Answer ---\n5 * * * *\n--------------")
            return True

        mock_ask.side_effect = side_effect

        result = await self.manager.generate("Every hour at minute 5")
        self.assertEqual(result, "5 * * * *")

if __name__ == '__main__':
    unittest.main()
