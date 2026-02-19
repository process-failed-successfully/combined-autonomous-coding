import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Input, Select, Label, DataTable
from shared.tui_unit import UnitLabTab


class TestUnitLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.patcher = patch("shared.tui_unit.UnitLabManager")
        self.MockManager = self.patcher.start()

        self.tab = UnitLabTab()
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        self.notify_patcher = patch.object(self.tab, 'notify')
        self.mock_notify = self.notify_patcher.start()

        self.query_one_patcher = patch.object(self.tab, 'query_one')
        self.mock_query_one = self.query_one_patcher.start()

    async def asyncTearDown(self):
        self.patcher.stop()
        self.notify_patcher.stop()
        self.query_one_patcher.stop()

    def test_update_result_success(self):
        # Mock Inputs
        val_input = MagicMock(spec=Input)
        val_input.value = "10"
        from_sel = MagicMock(spec=Select)
        from_sel.value = "m"
        to_sel = MagicMock(spec=Select)
        to_sel.value = "km"
        lbl = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#unit-value-input":
                return val_input
            if selector == "#unit-from-select":
                return from_sel
            if selector == "#unit-to-select":
                return to_sel
            if selector == "#unit-result-label":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.mock_manager.convert.return_value = "0.01"

        # Run
        self.tab.update_result()

        # Verify
        self.mock_manager.convert.assert_called_with(10.0, "m", "km")
        lbl.update.assert_called()
        args, _ = lbl.update.call_args
        self.assertIn("0.01", args[0])

    def test_update_result_error(self):
        # Mock Inputs
        val_input = MagicMock(spec=Input)
        val_input.value = "abc"
        from_sel = MagicMock(spec=Select)
        from_sel.value = "m"
        to_sel = MagicMock(spec=Select)
        to_sel.value = "km"
        lbl = MagicMock(spec=Label)

        def query_side_effect(selector, type=None):
            if selector == "#unit-value-input":
                return val_input
            if selector == "#unit-from-select":
                return from_sel
            if selector == "#unit-to-select":
                return to_sel
            if selector == "#unit-result-label":
                return lbl
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        # Run
        self.tab.update_result()

        # Verify
        self.mock_manager.convert.assert_not_called()
        lbl.update.assert_called_with("Invalid Number")

    def test_on_swap(self):
        from_sel = MagicMock(spec=Select)
        from_sel.value = "m"
        to_sel = MagicMock(spec=Select)
        to_sel.value = "km"

        def query_side_effect(selector, type=None):
            if selector == "#unit-from-select":
                return from_sel
            if selector == "#unit-to-select":
                return to_sel
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.tab.on_swap()

        self.assertEqual(from_sel.value, "km")
        self.assertEqual(to_sel.value, "m")

    def test_on_mount(self):
        self.mock_manager.get_categories.return_value = ["length", "mass"]
        cat_select = MagicMock(spec=Select)

        def query_side_effect(selector, type=None):
            if selector == "#unit-category-select":
                return cat_select
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.tab.on_mount()

        cat_select.set_options.assert_called()
        self.assertEqual(cat_select.value, "length")

    def test_on_category_changed(self):
        event = MagicMock()
        event.value = "mass"

        self.mock_manager.get_units_in_category.return_value = ["kg", "g"]

        from_sel = MagicMock(spec=Select)
        to_sel = MagicMock(spec=Select)
        val_input = MagicMock(spec=Input)
        val_input.value = "10"
        lbl = MagicMock(spec=Label)
        table = MagicMock(spec=DataTable)

        def query_side_effect(selector, type=None):
            if selector == "#unit-from-select":
                return from_sel
            if selector == "#unit-to-select":
                return to_sel
            if selector == "#unit-value-input":
                return val_input
            if selector == "#unit-result-label":
                return lbl
            if selector == "#unit-ref-table":
                return table
            return MagicMock()
        self.mock_query_one.side_effect = query_side_effect

        self.tab.on_category_changed(event)

        self.assertEqual(self.tab.current_category, "mass")
        self.mock_manager.get_units_in_category.assert_called_with("mass")
        from_sel.set_options.assert_called()
        self.assertEqual(from_sel.value, "kg")
        self.assertEqual(to_sel.value, "g")


if __name__ == "__main__":
    unittest.main()
