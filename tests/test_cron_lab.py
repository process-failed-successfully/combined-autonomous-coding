import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
import sys
import asyncio

# Setup mocks BEFORE importing shared.cron_lab
mock_ask_logic = AsyncMock()
sys.modules['shared.ask'] = MagicMock()
sys.modules['shared.ask'].run_ask_logic = mock_ask_logic

from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp")
        self.manager = CronLabManager(self.project_dir)
        mock_ask_logic.reset_mock()

    def test_validate_valid(self):
        valid, msg = self.manager.validate("*/5 * * * *")
        self.assertTrue(valid)
        self.assertIn("Valid", msg)

    def test_validate_invalid(self):
        valid, msg = self.manager.validate("invalid")
        self.assertFalse(valid)
        self.assertIn("Invalid", msg)

    def test_validate_empty(self):
        valid, msg = self.manager.validate("")
        self.assertFalse(valid)
        self.assertIn("Empty", msg)

    def test_get_next_runs(self):
        runs = self.manager.get_next_runs("*/15 * * * *", count=3)
        self.assertEqual(len(runs), 3)
        self.assertTrue(runs[0] < runs[1] < runs[2])

    def test_get_next_runs_invalid(self):
        runs = self.manager.get_next_runs("invalid")
        self.assertEqual(runs, [])

    def test_generate_expression(self):
        # Configure the mock to print to stdout when awaited
        async def side_effect(*args, **kwargs):
            print("\n--- Answer ---\n0 9 * * 1\n--------------")
            return True

        mock_ask_logic.side_effect = side_effect

        result = asyncio.run(self.manager.generate_expression("Every Monday at 9am"))
        self.assertEqual(result, "0 9 * * 1")
        mock_ask_logic.assert_called_once()

    def test_explain_expression(self):
        async def side_effect(*args, **kwargs):
            print("\n--- Answer ---\nRuns every 5 minutes.\n--------------")
            return True

        mock_ask_logic.side_effect = side_effect

        result = asyncio.run(self.manager.explain_expression("*/5 * * * *"))
        self.assertEqual(result, "Runs every 5 minutes.")
        mock_ask_logic.assert_called_once()

if __name__ == '__main__':
    unittest.main()
