import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import DataTable, Input, RichLog, Static

from shared.tui_math import MathLabTab


class TestMathLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Patch MathLabManager at the source where it is imported in tui_math
        self.patcher = patch("shared.tui_math.MathLabManager")
        self.MockManager = self.patcher.start()

        # Instantiate the tab
        # We need to mock super().__init__ if Container does complex stuff,
        # but let's try relying on standard behavior or if it fails we mock Container.
        # Textual widgets often need an app context for some operations but __init__ might be safe.

        # We might need to patch Container if it fails.
        # Let's assume it works like NetDiagTab test.
        self.tab = MathLabTab()
        self.mock_manager = self.MockManager.return_value
        # Ensure the tab uses our mock instance (it should, based on __init__)
        self.tab.manager = self.mock_manager

        # Mock Textual UI methods using patch.object to satisfy mypy
        self.notify_patcher = patch.object(self.tab, 'notify')
        self.mock_notify = self.notify_patcher.start()

        self.query_one_patcher = patch.object(self.tab, 'query_one')
        self.mock_query_one = self.query_one_patcher.start()

    async def asyncTearDown(self):
        self.patcher.stop()
        self.notify_patcher.stop()
        self.query_one_patcher.stop()

    async def test_evaluate_expression_success(self):
        # Mock Inputs
        expr_input = MagicMock(spec=Input)
        expr_input.value = "2 + 2"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-math-eval":
                return expr_input
            if selector == "#log-math-eval":
                return log
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.evaluate.return_value = 4

        # Run
        await self.tab.evaluate_expression()

        # Verify
        self.mock_manager.evaluate.assert_called_with("2 + 2")
        log.write.assert_called()
        args, _ = log.write.call_args
        self.assertIn("4", args[0])
        # Verify input clear
        self.assertEqual(expr_input.value, "")

    async def test_evaluate_expression_error(self):
        # Mock Inputs
        expr_input = MagicMock(spec=Input)
        expr_input.value = "invalid"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-math-eval":
                return expr_input
            if selector == "#log-math-eval":
                return log
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.evaluate.side_effect = ValueError("Bad syntax")

        # Run
        await self.tab.evaluate_expression()

        # Verify
        log.write.assert_called()
        args, _ = log.write.call_args
        self.assertIn("Error", args[0])
        self.mock_notify.assert_called_with("Error: Bad syntax", severity="error")

    async def test_calculate_statistics(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "1, 2, 3"
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#input-math-stats":
                return input_widget
            if selector == "#table-math-stats":
                return table
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager Result
        self.mock_manager.calculate_stats.return_value = {"mean": 2.0, "max": 3.0}

        # Run
        await self.tab.calculate_statistics()

        # Verify
        self.mock_manager.calculate_stats.assert_called()
        call_args = self.mock_manager.calculate_stats.call_args
        self.assertEqual(call_args[0][0], [1.0, 2.0, 3.0])

        table.clear.assert_called()
        self.assertEqual(table.add_row.call_count, 2)
        self.mock_notify.assert_called_with("Statistics calculated.")

    async def test_check_prime_true(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "7"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-math-prime":
                return input_widget
            if selector == "#lbl-math-prime-result":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager Result (asyncio.to_thread will call this)
        self.mock_manager.is_prime.return_value = True

        # Run
        await self.tab.check_prime()

        # Verify
        self.mock_manager.is_prime.assert_called_with(7)
        lbl.update.assert_any_call("Checking...")
        # Check final update
        args_list = lbl.update.call_args_list
        final_call_arg = args_list[-1][0][0]
        self.assertIn("is prime", final_call_arg)

    async def test_find_next_prime(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "10"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-math-prime":
                return input_widget
            if selector == "#lbl-math-prime-result":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.next_prime.return_value = 11

        # Run
        await self.tab.find_next_prime()

        # Verify
        self.mock_manager.next_prime.assert_called_with(10)
        args_list = lbl.update.call_args_list
        final_call_arg = args_list[-1][0][0]
        self.assertIn("11", final_call_arg)

    async def test_find_prime_factors(self):
        # Mock Inputs
        input_widget = MagicMock(spec=Input)
        input_widget.value = "12"
        lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-math-prime":
                return input_widget
            if selector == "#lbl-math-prime-result":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Mock Manager
        self.mock_manager.prime_factors.return_value = [2, 2, 3]

        # Run
        await self.tab.find_prime_factors()

        # Verify
        self.mock_manager.prime_factors.assert_called_with(12)
        args_list = lbl.update.call_args_list
        final_call_arg = args_list[-1][0][0]
        self.assertIn("[2, 2, 3]", final_call_arg)


if __name__ == "__main__":
    unittest.main()
