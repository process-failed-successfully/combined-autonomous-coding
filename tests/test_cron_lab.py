import sys
from unittest.mock import MagicMock

# Mock dependencies that might be missing or problematic in test env
# This ensures we are unit testing CronLabManager logic, not the whole dependency tree
sys.modules['psutil'] = MagicMock()
sys.modules['prometheus_client'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['docker'] = MagicMock()
sys.modules['git'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['openai'] = MagicMock()
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.aiplatform'] = MagicMock()

import unittest
from datetime import datetime
from unittest.mock import patch, AsyncMock
from pathlib import Path

# Ensure shared module is in path
sys.path.append(".")

from shared.cron_lab import CronLabManager

class TestCronLabManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp")
        self.manager = CronLabManager(self.project_dir)

    def test_get_next_runs_success(self):
        expression = "*/15 * * * *"
        result = self.manager.get_next_runs(expression, count=3)

        self.assertTrue(result["success"], f"Failed: {result.get('error')}")
        self.assertEqual(result["expression"], expression)
        self.assertEqual(len(result["next_runs"]), 3)
        self.assertIsInstance(result["next_runs"][0], datetime)

    def test_get_next_runs_invalid(self):
        expression = "invalid cron"
        result = self.manager.get_next_runs(expression)

        self.assertFalse(result["success"])
        self.assertIn("error", result)

    @patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_explain_expression(self, mock_ask):
        async def mock_print(*args, **kwargs):
            print("It runs every 15 minutes.")

        mock_ask.side_effect = mock_print

        response = await self.manager.explain_expression("*/15 * * * *")
        self.assertIn("It runs every 15 minutes.", response)

    @patch("shared.cron_lab.run_ask_logic", new_callable=AsyncMock)
    async def test_generate_expression(self, mock_ask):
        async def mock_print(*args, **kwargs):
            print("```\n*/5 * * * *\n```")

        mock_ask.side_effect = mock_print

        response = await self.manager.generate_expression("Every 5 minutes")
        self.assertIn("*/5 * * * *", response)

if __name__ == '__main__':
    unittest.main()
