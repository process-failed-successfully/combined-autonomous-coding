import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, RichLog, Static
from shared.tui_calc import CalcLabTab


class TestCalcLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_calc.CalcLabManager")
        self.MockManager = self.patcher.start()

        self.tab = CalcLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        # Set up variables dict since it is accessed directly
        self.mock_manager.variables = {}

        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    async def test_evaluate_expression_success(self):
        expr_input = MagicMock(spec=Input)
        expr_input.value = "0xFF + 1"
        log = MagicMock(spec=RichLog)
        vars_lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-calc-eval":
                return expr_input
            if selector == "#log-calc-eval":
                return log
            if selector == "#lbl-calc-vars":
                return vars_lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.evaluate.return_value = 256
        self.mock_manager.format_result.return_value = "Dec: 256\nHex: 0x100"

        await self.tab.evaluate_expression()

        self.mock_manager.evaluate.assert_called_with("0xFF + 1")
        self.mock_manager.format_result.assert_called_with(256)

        # Log update
        log.write.assert_called()
        args, _ = log.write.call_args
        self.assertIn("0xFF + 1", args[0])
        self.assertIn("0x100", args[0])

        # Verify input is cleared
        self.assertEqual(expr_input.value, "")

        # Verify variables display
        vars_lbl.update.assert_called_with("{}")

    async def test_evaluate_expression_variables(self):
        expr_input = MagicMock(spec=Input)
        expr_input.value = "x = 10"
        log = MagicMock(spec=RichLog)
        vars_lbl = MagicMock(spec=Static)

        def query_side_effect(selector, type=None):
            if selector == "#input-calc-eval":
                return expr_input
            if selector == "#log-calc-eval":
                return log
            if selector == "#lbl-calc-vars":
                return vars_lbl
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.evaluate.return_value = 10
        self.mock_manager.format_result.return_value = "10"
        self.mock_manager.variables = {'x': 10}

        await self.tab.evaluate_expression()

        # Verify special '_' assignment
        self.assertEqual(self.mock_manager.variables['_'], 10)

        # Variables label shouldn't show '_'
        vars_lbl.update.assert_called()
        args, _ = vars_lbl.update.call_args
        self.assertIn("'x': 10", args[0])
        self.assertNotIn("'_'", args[0])

    async def test_evaluate_expression_error(self):
        expr_input = MagicMock(spec=Input)
        expr_input.value = "invalid"
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#input-calc-eval":
                return expr_input
            if selector == "#log-calc-eval":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        self.mock_manager.evaluate.side_effect = ValueError("Bad syntax")

        await self.tab.evaluate_expression()

        log.write.assert_called()
        args, _ = log.write.call_args
        self.assertIn("Error: Bad syntax", args[0])
        self.tab.notify.assert_called_with("Error: Bad syntax", severity="error")

    async def test_clear_log(self):
        log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if selector == "#log-calc-eval":
                return log
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        class MockEvent:
            class MockButton:
                id = "btn-calc-clear"
            button = MockButton()

        await self.tab.on_button_pressed(MockEvent())

        log.clear.assert_called()


if __name__ == "__main__":
    unittest.main()
