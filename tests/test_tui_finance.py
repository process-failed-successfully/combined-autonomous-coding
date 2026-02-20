import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, RichLog
# Import the class under test
from shared.tui_finance import FinanceLabTab


class TestFinanceLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch FinanceLabManager at the source where it is imported in tui_finance
        self.patcher = patch("shared.tui_finance.FinanceLabManager")
        self.MockManager = self.patcher.start()

        self.tab = FinanceLabTab()
        self.mock_manager = self.MockManager.return_value
        # Ensure the tab uses our mock instance
        self.tab.manager = self.mock_manager

        # Mock Textual UI methods
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_calculate_loan(self):
        # Mock Inputs
        principal = MagicMock(spec=Input)
        principal.value = "1000"
        rate = MagicMock(spec=Input)
        rate.value = "5"
        term = MagicMock(spec=Input)
        term.value = "10"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-loan-principal":
                return principal
            if selector == "#input-loan-rate":
                return rate
            if selector == "#input-loan-term":
                return term
            if selector == "#log-loan-result":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_loan_payment.return_value = "Loan Summary..."

        await self.tab.calculate_loan()

        self.mock_manager.calculate_loan_payment.assert_called_with(1000.0, 5.0, 10)
        log.write.assert_called_with("Loan Summary...")

    async def test_calculate_compound(self):
        # Mock Inputs
        principal = MagicMock(spec=Input)
        principal.value = "1000"
        rate = MagicMock(spec=Input)
        rate.value = "5"
        time = MagicMock(spec=Input)
        time.value = "10"
        freq = MagicMock(spec=Input)
        freq.value = "12"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-compound-principal":
                return principal
            if selector == "#input-compound-rate":
                return rate
            if selector == "#input-compound-time":
                return time
            if selector == "#input-compound-freq":
                return freq
            if selector == "#log-compound-result":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_compound_interest.return_value = "Compound Summary..."

        await self.tab.calculate_compound()

        self.mock_manager.calculate_compound_interest.assert_called_with(1000.0, 5.0, 10, 12)
        log.write.assert_called_with("Compound Summary...")

    async def test_calculate_npv(self):
        rate = MagicMock(spec=Input)
        rate.value = "5"
        flows = MagicMock(spec=Input)
        flows.value = "-1000, 200, 300, 500"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-npv-rate":
                return rate
            if selector == "#input-npv-flows":
                return flows
            if selector == "#log-npv-result":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_npv.return_value = "NPV Result..."

        await self.tab.calculate_npv()

        self.mock_manager.calculate_npv.assert_called_with(5.0, [-1000.0, 200.0, 300.0, 500.0])
        log.write.assert_called_with("NPV Result...")

    async def test_calculate_roi(self):
        initial = MagicMock(spec=Input)
        initial.value = "1000"
        final = MagicMock(spec=Input)
        final.value = "1500"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-roi-initial":
                return initial
            if selector == "#input-roi-final":
                return final
            if selector == "#log-roi-result":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_roi.return_value = "ROI Result..."

        await self.tab.calculate_roi()

        self.mock_manager.calculate_roi.assert_called_with(1000.0, 1500.0)
        log.write.assert_called_with("ROI Result...")

    async def test_calculate_break_even(self):
        fixed = MagicMock(spec=Input)
        fixed.value = "10000"
        variable = MagicMock(spec=Input)
        variable.value = "5"
        price = MagicMock(spec=Input)
        price.value = "10"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-be-fixed":
                return fixed
            if selector == "#input-be-variable":
                return variable
            if selector == "#input-be-price":
                return price
            if selector == "#log-be-result":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_break_even.return_value = "Break-Even Result..."

        await self.tab.calculate_break_even()

        self.mock_manager.calculate_break_even.assert_called_with(10000.0, 5.0, 10.0)
        log.write.assert_called_with("Break-Even Result...")

    async def test_calculate_inflation(self):
        value = MagicMock(spec=Input)
        value.value = "100"
        rate = MagicMock(spec=Input)
        rate.value = "3"
        years = MagicMock(spec=Input)
        years.value = "10"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-inf-value":
                return value
            if selector == "#input-inf-rate":
                return rate
            if selector == "#input-inf-years":
                return years
            if selector == "#log-inf-result":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.calculate_inflation.return_value = "Inflation Result..."

        await self.tab.calculate_inflation()

        self.mock_manager.calculate_inflation.assert_called_with(100.0, 3.0, 10)
        log.write.assert_called_with("Inflation Result...")


if __name__ == "__main__":
    unittest.main()
