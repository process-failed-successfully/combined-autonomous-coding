import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from shared.cron_lab import CronLabManager
from datetime import datetime

class TestCronLabManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.manager = CronLabManager()

    def test_parse_valid(self):
        # 5 parts
        result = self.manager.parse("0 12 * * 1-5")
        self.assertTrue(result["success"])
        self.assertEqual(result["minute"], "0")
        self.assertEqual(result["hour"], "12")
        self.assertEqual(result["day_of_month"], "*")
        self.assertEqual(result["month"], "*")
        self.assertEqual(result["day_of_week"], "1-5")

        # 6 parts
        result6 = self.manager.parse("0 0 12 * * 1-5")
        self.assertTrue(result6["success"])
        self.assertEqual(result6["second"], "0")
        self.assertEqual(result6["minute"], "0")
        self.assertEqual(result6["hour"], "12")
        self.assertEqual(result6["day_of_month"], "*")
        self.assertEqual(result6["month"], "*")
        self.assertEqual(result6["day_of_week"], "1-5")

    def test_parse_invalid(self):
        result = self.manager.parse("invalid")
        self.assertFalse(result["success"])
        self.assertIn("Invalid cron expression", result["error"])

    def test_get_next_occurrences_valid(self):
        # Every minute
        expression = "* * * * *"
        result = self.manager.get_next_occurrences(expression, count=2)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["occurrences"]), 2)

        # Verify valid isoformat dates
        try:
            datetime.fromisoformat(result["occurrences"][0])
        except ValueError:
            self.fail("Occurrences are not valid ISO format dates")

    def test_get_next_occurrences_invalid(self):
        expression = "invalid"
        result = self.manager.get_next_occurrences(expression)
        self.assertFalse(result["success"])
        self.assertIn("Invalid cron expression", result["error"])

    @patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_explain_expression(self, mock_ask):
        mock_ask.return_value = True
        result = await self.manager.explain_expression("* * * * *", MagicMock())
        self.assertTrue(result)
        mock_ask.assert_called_once()

    @patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_generate_expression(self, mock_ask):
        mock_ask.return_value = True
        result = await self.manager.generate_expression("every day at noon", MagicMock())
        self.assertTrue(result)
        mock_ask.assert_called_once()

class TestCronLabCLI(unittest.IsolatedAsyncioTestCase):
    @patch("main.run_tui")
    async def test_run_cron_lab_tui(self, mock_run_tui):
        from main import run_cron_lab
        args = MagicMock()
        args.action = "tui"

        await run_cron_lab(args)

        mock_run_tui.assert_called_once_with(args, start_tab="tab-cron")
