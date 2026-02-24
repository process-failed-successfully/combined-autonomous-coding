import unittest
from unittest.mock import MagicMock, patch
from textual.widgets import Label, Button, ListView, ListItem, RichLog, TextArea, Input
from shared.tui_pipeline import PipelineLabTab

class TestPipelineLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = PipelineLabTab()
        self.tab.notify = MagicMock()

    async def test_add_step(self):
        # Mock query_one
        mock_ops_list = MagicMock(spec=ListView)
        mock_ops_list.index = 0
        mock_ops_list.children = [MagicMock()]
        mock_ops_list.children[0].query_one.return_value.renderable = "upper"

        mock_arg_input = MagicMock(spec=Input)
        mock_arg_input.value = ""

        mock_steps_list = MagicMock(spec=ListView)

        mock_input_area = MagicMock(spec=TextArea)
        mock_input_area.text = "hello"

        mock_output_log = MagicMock(spec=RichLog)

        def query_one_side_effect(selector, type=None):
            if selector == "#pipe-ops-list":
                return mock_ops_list
            if selector == "#pipe-op-arg":
                return mock_arg_input
            if selector == "#pipe-steps-list":
                return mock_steps_list
            if selector == "#pipe-input":
                return mock_input_area
            if selector == "#pipe-output":
                return mock_output_log
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Action: Add Step
        self.tab.add_step()

        # Verify step added
        self.assertEqual(self.tab.pipeline_steps, ["upper"])
        mock_steps_list.clear.assert_called()
        mock_steps_list.append.assert_called()

        # Verify output updated
        # "hello" -> upper -> "HELLO"
        mock_output_log.clear.assert_called()
        mock_output_log.write.assert_called_with("HELLO")

    async def test_add_step_with_arg(self):
        mock_ops_list = MagicMock(spec=ListView)
        mock_ops_list.index = 0
        mock_ops_list.children = [MagicMock()]
        mock_ops_list.children[0].query_one.return_value.renderable = "grep"

        mock_arg_input = MagicMock(spec=Input)
        mock_arg_input.value = "foo"

        mock_steps_list = MagicMock(spec=ListView)

        mock_input_area = MagicMock(spec=TextArea)
        mock_input_area.text = "foo\nbar"

        mock_output_log = MagicMock(spec=RichLog)

        def query_one_side_effect(selector, type=None):
            if selector == "#pipe-ops-list":
                return mock_ops_list
            if selector == "#pipe-op-arg":
                return mock_arg_input
            if selector == "#pipe-steps-list":
                return mock_steps_list
            if selector == "#pipe-input":
                return mock_input_area
            if selector == "#pipe-output":
                return mock_output_log
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Action: Add Step
        self.tab.add_step()

        # Verify step added
        self.assertEqual(self.tab.pipeline_steps, ["grep foo"])

        # Verify output updated
        # "foo\nbar" -> grep foo -> ["foo"]
        # The pipeline manager returns list for grep usually?
        # Let's check manager implementation. grep returns list.
        # update_output handles list by json dumping.
        mock_output_log.write.assert_called()
        call_arg = mock_output_log.write.call_args[0][0]
        self.assertIn("foo", call_arg)
        self.assertNotIn("bar", call_arg)

    async def test_remove_step(self):
        self.tab.pipeline_steps = ["upper", "lower"]

        mock_steps_list = MagicMock(spec=ListView)
        mock_steps_list.index = 0

        mock_input_area = MagicMock(spec=TextArea)
        mock_input_area.text = "hello"

        mock_output_log = MagicMock(spec=RichLog)

        def query_one_side_effect(selector, type=None):
            if selector == "#pipe-steps-list":
                return mock_steps_list
            if selector == "#pipe-input":
                return mock_input_area
            if selector == "#pipe-output":
                return mock_output_log
            return MagicMock()

        self.tab.query_one = MagicMock(side_effect=query_one_side_effect)

        # Action: Remove Step at index 0
        self.tab.remove_step()

        self.assertEqual(self.tab.pipeline_steps, ["lower"])
        mock_output_log.write.assert_called_with("hello") # lower("hello") -> "hello"

if __name__ == "__main__":
    unittest.main()
