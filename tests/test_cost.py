import unittest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from shared.cost import CostCalculator


class TestCostCalculator(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.mock_config = {"budget_limit": 10.0}

    @patch("shared.cost.load_config_from_file")
    def test_get_pricing(self, mock_load):
        calc = CostCalculator(self.project_dir)

        # Exact match
        price = calc.get_pricing("gemini-1.5-pro")
        self.assertEqual(price["input"], 3.50)

        # Fuzzy match
        price = calc.get_pricing("gemini-1.5-flash-001")
        self.assertEqual(price["input"], 0.35)

        # Fallback
        price = calc.get_pricing("unknown-model")
        self.assertEqual(price["input"], 0.35)

    @patch("shared.cost.load_config_from_file")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.iterdir")
    def test_calculate_run_cost(self, mock_iter, mock_exists, mock_load):
        mock_exists.return_value = True

        # Mock finding log file
        mock_log_file = MagicMock()
        mock_log_file.name = "run_123.log"
        mock_log_file.suffix = ".log"
        mock_iter.return_value = [mock_log_file]

        # Mock reading log file
        log_content = """
        Model: gemini-1.5-pro
        Input Tokens: 1000
        Output Tokens: 500
        """
        with patch("builtins.open", mock_open(read_data=log_content)):
            calc = CostCalculator(self.project_dir)
            result = calc.calculate_run_cost("run_123")

            self.assertEqual(result["model"], "gemini-1.5-pro")
            self.assertEqual(result["input_tokens"], 1000)
            self.assertEqual(result["output_tokens"], 500)
            # 1000/1M * 3.5 + 500/1M * 10.5 = 0.0035 + 0.00525 = 0.00875
            self.assertAlmostEqual(result["total_cost"], 0.00875)

    @patch("shared.cost.load_config_from_file")
    @patch("shared.cost.CostCalculator.calculate_run_cost")
    @patch("pathlib.Path.exists")
    def test_check_budget(self, mock_exists, mock_calc_run, mock_load):
        mock_load.return_value = self.mock_config  # limit 10.0
        mock_exists.return_value = True  # Pretend .agent_history exists
        calc = CostCalculator(self.project_dir)

        with patch("builtins.open", mock_open(read_data="run1\nrun2")):
            # run1 cost = 4.0, run2 cost = 5.0. Total = 9.0 (90%) -> WARNING
            mock_calc_run.side_effect = [
                {"total_cost": 4.0},
                {"total_cost": 5.0}
            ]

            status = calc.check_budget()
            self.assertEqual(status["current"], 9.0)
            self.assertEqual(status["status"], "WARNING")
            self.assertEqual(status["percent"], 90.0)

    @patch("shared.cost.load_config_from_file")
    @patch("shared.cost.CostCalculator.calculate_run_cost")
    @patch("pathlib.Path.exists")
    def test_check_budget_exceeded(self, mock_exists, mock_calc_run, mock_load):
        mock_load.return_value = self.mock_config  # limit 10.0
        mock_exists.return_value = True
        calc = CostCalculator(self.project_dir)

        with patch("builtins.open", mock_open(read_data="run1")):
            mock_calc_run.return_value = {"total_cost": 11.0}

            status = calc.check_budget()
            self.assertEqual(status["status"], "EXCEEDED")
