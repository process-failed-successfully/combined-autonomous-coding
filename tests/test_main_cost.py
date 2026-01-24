import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import io
import main


# Helper to create a dummy args object
class Args:
    def __init__(self, run_id=None, project_dir=Path("."), budget=False):
        self.run_id = run_id
        self.project_dir = project_dir
        self.budget = budget


class TestMainCost(unittest.TestCase):
    def setUp(self):
        self.captured_output = io.StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("main.CostCalculator")
    def test_run_cost_success(self, mock_calc_cls):
        # Mock setup
        mock_calc = mock_calc_cls.return_value
        mock_calc.calculate_run_cost.return_value = {
            "run_id": "test-run",
            "model": "gemini-1.5-pro",
            "input_tokens": 1000,
            "output_tokens": 500,
            "input_cost": 0.0035,
            "output_cost": 0.00525,
            "total_cost": 0.00875
        }

        args = Args(run_id="test-run")
        with self.assertRaises(SystemExit) as cm:
            main.run_cost(args)

        self.assertEqual(cm.exception.code, 0)

        output = self.captured_output.getvalue()
        self.assertIn("Cost Estimate for Run: test-run", output)
        self.assertIn("gemini-1.5-pro", output)  # Match just model name
        self.assertIn("1,000", output)
        self.assertIn("500", output)
        self.assertIn("$0.0088", output)

    @patch("main.CostCalculator")
    def test_run_cost_budget(self, mock_calc_cls):
        mock_calc = mock_calc_cls.return_value
        mock_calc.check_budget.return_value = {
            "current": 5.0,
            "limit": 10.0,
            "remaining": 5.0,
            "percent": 50.0,
            "status": "OK"
        }
        # Also mock run cost since it continues to calculate run cost
        mock_calc.calculate_run_cost.return_value = {
            "run_id": "test-run",
            "model": "gemini-1.5-pro",
            "input_tokens": 1000,
            "output_tokens": 500,
            "input_cost": 0.0035,
            "output_cost": 0.00525,
            "total_cost": 0.00875
        }

        args = Args(budget=True, run_id="test-run")  # Provide run_id to avoid file lookup
        with self.assertRaises(SystemExit) as cm:
            main.run_cost(args)

        self.assertEqual(cm.exception.code, 0)
        output = self.captured_output.getvalue()
        self.assertIn("Budget Status", output)
        self.assertIn("OK", output)
        self.assertIn("50.0%", output)

    @patch("main.CostCalculator")
    def test_run_cost_error(self, mock_calc_cls):
        mock_calc = mock_calc_cls.return_value
        mock_calc.calculate_run_cost.return_value = {"error": "No file found"}

        args = Args(run_id="missing-run")
        with self.assertRaises(SystemExit) as cm:
            # We capture stderr too because it prints error there
            with patch('sys.stderr', new=io.StringIO()):
                main.run_cost(args)

        self.assertEqual(cm.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
