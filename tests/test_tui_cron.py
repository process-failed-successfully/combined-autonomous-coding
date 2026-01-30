import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.tui_cron import CronLabTab

class TestCronLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path(".")
        self.tab = CronLabTab(self.project_dir)

        # Mock notify
        self.tab.notify = MagicMock()

        # Mock query_one
        self.mock_query_one = MagicMock()
        self.tab.query_one = self.mock_query_one

    @patch("shared.tui_cron.CronLabManager")
    def test_calculate_next_success(self, mock_manager_cls):
        # Setup mock manager
        mock_manager = mock_manager_cls.return_value
        mock_manager.get_next_occurrences.return_value = {
            "success": True,
            "occurrences": ["2023-10-27 10:00:00", "2023-10-27 10:05:00"]
        }
        self.tab.manager = mock_manager

        # Setup mock widgets
        mock_input_expr = MagicMock()
        mock_input_expr.value = "*/5 * * * *"
        mock_input_count = MagicMock()
        mock_input_count.value = "2"
        mock_output = MagicMock()

        def query_side_effect(selector, type=None):
            if selector == "#cron-expression": return mock_input_expr
            if selector == "#cron-count": return mock_input_count
            if selector == "#cron-output": return mock_output
            return MagicMock()

        self.mock_query_one.side_effect = query_side_effect

        # Call method
        self.tab.calculate_next()

        # Verify
        mock_manager.get_next_occurrences.assert_called_with("*/5 * * * *", 2)
        mock_output.clear.assert_called()
        # Should write occurrences
        self.assertTrue(mock_output.write.called)

    @patch("shared.tui_cron.run_ask_logic", new_callable=AsyncMock)
    async def test_explain_cron(self, mock_ask):
        # Setup mock widgets
        mock_input_expr = MagicMock()
        mock_input_expr.value = "0 0 * * *"
        mock_agent = MagicMock()
        mock_agent.value = "gemini"
        mock_output = MagicMock()

        def query_side_effect(selector, type=None):
            if selector == "#cron-expression": return mock_input_expr
            if selector == "#cron-agent": return mock_agent
            if selector == "#cron-output": return mock_output
            return MagicMock()

        self.mock_query_one.side_effect = query_side_effect

        # Call method
        await self.tab.explain_cron()

        # Verify ask logic called
        mock_ask.assert_called()
        args, kwargs = mock_ask.call_args
        self.assertIn("Explain the following cron expression", kwargs['query'])
        self.assertEqual(kwargs['agent_type'], "gemini")

    @patch("shared.tui_cron.run_ask_logic", new_callable=AsyncMock)
    async def test_generate_cron(self, mock_ask):
        # Setup mock widgets
        mock_desc = MagicMock()
        mock_desc.text = "Every day at noon"
        mock_agent = MagicMock()
        mock_agent.value = "gemini"
        mock_output = MagicMock()

        def query_side_effect(selector, type=None):
            if selector == "#cron-description": return mock_desc
            if selector == "#cron-agent": return mock_agent
            if selector == "#cron-output": return mock_output
            return MagicMock()

        self.mock_query_one.side_effect = query_side_effect

        # Call method
        await self.tab.generate_cron()

        # Verify ask logic called
        mock_ask.assert_called()
        args, kwargs = mock_ask.call_args
        self.assertIn("Generate a standard cron expression", kwargs['query'])
        self.assertIn("Every day at noon", kwargs['query'])

if __name__ == "__main__":
    unittest.main()
