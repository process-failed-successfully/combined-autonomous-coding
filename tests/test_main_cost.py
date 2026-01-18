import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import io
import main

# Helper to create a dummy args object
class Args:
    def __init__(self, run_id=None, project_dir=Path(".")):
        self.run_id = run_id
        self.project_dir = project_dir

class TestMainCost(unittest.TestCase):
    def setUp(self):
        self.captured_output = io.StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    @patch("main._find_metrics_file")
    @patch("main._parse_metrics")
    def test_run_cost_success(self, mock_parse, mock_find):
        # Mock setup
        mock_find.return_value = Path("dummy_metrics.txt")
        mock_parse.return_value = {
            "Run ID": "test-run",
            "Model": "gemini-1.5-pro",
            "LLM Tokens Used": 1500,
            "llm_tokens_total__gemini-1.5-pro__input": 1000,
            "llm_tokens_total__gemini-1.5-pro__output": 500
        }

        args = Args(run_id="test-run")
        with self.assertRaises(SystemExit) as cm:
            main.run_cost(args)

        self.assertEqual(cm.exception.code, 0)

        output = self.captured_output.getvalue()
        self.assertIn("Cost Estimate for Run: test-run", output)
        self.assertIn("Model: gemini-1.5-pro", output)
        self.assertIn("Input Tokens:  1,000", output)
        self.assertIn("Output Tokens: 500", output)

        # Calculation:
        # Input: 1000/1M * 3.50 = 0.0035
        # Output: 500/1M * 10.50 = 0.00525
        # Total: 0.00875
        self.assertIn("Total:  $0.0088", output) # Formatted to .4f

    @patch("main._find_metrics_file")
    @patch("main._parse_metrics")
    def test_run_cost_fallback(self, mock_parse, mock_find):
        # Mock setup - legacy format (no breakdown)
        mock_find.return_value = Path("dummy_metrics.txt")
        mock_parse.return_value = {
            "Run ID": "legacy-run",
            "Model": "gemini-1.5-flash",
            "LLM Tokens Used": 10000
        }

        args = Args(run_id="legacy-run")
        with self.assertRaises(SystemExit) as cm:
            main.run_cost(args)

        self.assertEqual(cm.exception.code, 0)

        output = self.captured_output.getvalue()
        self.assertIn("Assuming 75% input, 25% output", output)

        # Calculation:
        # Total: 10000
        # Input: 7500 => 7500/1M * 0.35 = 0.002625
        # Output: 2500 => 2500/1M * 1.05 = 0.002625
        # Total: 0.00525 -> 0.0052 (Banker's rounding)
        self.assertIn("Total:  $0.0052", output)

    @patch("main._find_metrics_file")
    def test_run_cost_no_file(self, mock_find):
        mock_find.return_value = None
        args = Args(run_id="missing-run")

        with self.assertRaises(SystemExit) as cm:
            # We capture stderr too because it prints error there
            with patch('sys.stderr', new=io.StringIO()) as fake_stderr:
                main.run_cost(args)

        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
