import unittest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402

from shared.finance_lab import FinanceLabManager, run_finance_lab_logic  # noqa: E402


class TestFinanceLab(unittest.TestCase):
    def setUp(self):
        self.manager = FinanceLabManager()

    def test_calculate_loan_payment(self):
        # Example: $100,000 loan, 5% annual rate, 30 years
        result = self.manager.calculate_loan_payment(100000, 5, 30)
        self.assertIn("Principal:      $100,000.00", result)
        self.assertIn("Monthly Payment: $536.82", result)
        self.assertIn("Total Payment:  $193,255.78", result)

        # Edge case: 0% interest
        result_zero = self.manager.calculate_loan_payment(10000, 0, 10)
        self.assertIn("Monthly Payment: $83.33", result_zero)
        self.assertIn("Total Interest: $0.00", result_zero)

        # Error case
        result_error = self.manager.calculate_loan_payment(-100, 5, 30)
        self.assertTrue(result_error.startswith("Error"))

    def test_calculate_compound_interest(self):
        # Example: $1,000, 5% rate, 10 years, monthly (12)
        result = self.manager.calculate_compound_interest(1000, 5, 10, 12)
        self.assertIn("Principal:      $1,000.00", result)
        self.assertIn("Future Value:   $1,647.01", result)  # 1000 * (1 + 0.05/12)^(120) = 1647.009...

        # Error case
        result_error = self.manager.calculate_compound_interest(1000, -5, 10, 12)
        self.assertTrue(result_error.startswith("Error"))

    def test_calculate_npv(self):
        # Rate 10%, flows [-1000, 200, 300, 400, 500]
        # NPV = -1000 + 200/1.1 + 300/1.21 + 400/1.331 + 500/1.4641
        # NPV = -1000 + 181.82 + 247.93 + 300.53 + 341.51 = 71.79
        flows = [-1000, 200, 300, 400, 500]
        result = self.manager.calculate_npv(10, flows)
        self.assertIn("Net Present Value: $71.78", result)  # slightly different rounding maybe?
        # Let's check with simpler values
        # Rate 0%, flows [-100, 150] -> NPV 50
        result_simple = self.manager.calculate_npv(0, [-100, 150])
        self.assertIn("Net Present Value: $50.00", result_simple)

    def test_calculate_roi(self):
        # Invest 1000, return 1500 -> 50% ROI
        result = self.manager.calculate_roi(1000, 1500)
        self.assertIn("ROI:                50.00%", result)
        self.assertIn("Net Profit/Loss:    $500.00", result)

        # Error case
        result_error = self.manager.calculate_roi(0, 100)
        self.assertTrue(result_error.startswith("Error"))

    def test_calculate_break_even(self):
        # Fixed 1000, Var 10, Price 20 -> Margin 10 -> BE Units 100
        result = self.manager.calculate_break_even(1000, 10, 20)
        self.assertIn("Break-Even Units:   100.00", result)
        self.assertIn("Break-Even Revenue: $2,000.00", result)

        # Error case
        result_error = self.manager.calculate_break_even(1000, 20, 10)  # Price < Var Cost
        self.assertTrue(result_error.startswith("Error"))

    def test_calculate_inflation(self):
        # $100, 3%, 5 years
        # Future value needed: 100 * 1.03^5 = 115.93
        # Purchasing power loss: 100 - (100 / 1.03^5) = 100 - 86.26 = 13.74
        result = self.manager.calculate_inflation(100, 3, 5)
        self.assertIn("Future Cost:    $115.93", result)
        self.assertIn("Purchasing Power Loss: $13.74", result)

    def test_run_finance_lab_logic(self):
        # Mock args
        args = MagicMock()
        args.action = "loan"
        args.principal = 100000.0
        args.rate = 5.0
        args.term = 30

        # We need to capture stdout
        from io import StringIO
        import sys
        saved_stdout = sys.stdout
        try:
            out = StringIO()
            sys.stdout = out
            success = run_finance_lab_logic(args)
            self.assertTrue(success)
            output = out.getvalue().strip()
            self.assertIn("Loan Summary:", output)
        finally:
            sys.stdout = saved_stdout

        # Test failure case
        args.action = "loan"
        args.principal = None  # Missing arg

        saved_stderr = sys.stderr
        try:
            err = StringIO()
            sys.stderr = err
            success = run_finance_lab_logic(args)
            self.assertFalse(success)
            output = err.getvalue().strip()
            self.assertIn("Error:", output)
        finally:
            sys.stderr = saved_stderr


if __name__ == '__main__':
    unittest.main()
