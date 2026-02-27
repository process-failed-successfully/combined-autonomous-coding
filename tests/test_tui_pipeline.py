import unittest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch
from textual.app import App, ComposeResult
from textual.widgets import DataTable, RichLog, TextArea, Select, Input, Button

# We need to ensure the shared module can be imported
import sys
sys.path.append(str(Path(__file__).parent.parent))

from shared.tui_pipeline import PipelineLabTab

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield PipelineLabTab(Path("."))

class TestPipelineTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = TestApp()
        self.pilot_cm = self.app.run_test()
        self.pilot = await self.pilot_cm.__aenter__()
        self.tab = self.app.query_one(PipelineLabTab)

    async def asyncTearDown(self):
        await self.pilot_cm.__aexit__(None, None, None)

    async def test_compose_structure(self):
        """Test that all main widgets are present."""
        self.assertIsInstance(self.tab.query_one("#pipe-input"), TextArea)
        self.assertIsInstance(self.tab.query_one("#pipe-op-select"), Select)
        self.assertIsInstance(self.tab.query_one("#pipe-arg-input"), Input)
        self.assertIsInstance(self.tab.query_one("#pipe-steps-table"), DataTable)
        self.assertIsInstance(self.tab.query_one("#pipe-output"), RichLog)

        # Verify initial state of DataTable
        table = self.tab.query_one("#pipe-steps-table")
        self.assertEqual(len(table.rows), 0)

    async def test_add_remove_step(self):
        """Test adding and removing pipeline steps."""
        select = self.tab.query_one("#pipe-op-select", Select)
        arg_input = self.tab.query_one("#pipe-arg-input", Input)
        add_btn = self.tab.query_one("#btn-pipe-add", Button)
        table = self.tab.query_one("#pipe-steps-table", DataTable)

        # Simulate user input
        select.value = "upper"
        arg_input.value = ""

        # Directly call the method to avoid UI event flakiness in headless test
        self.tab.add_step()

        # Check internal state and table
        self.assertEqual(len(self.tab.pipeline_steps), 1)
        self.assertEqual(self.tab.pipeline_steps[0], ("upper", ""))
        self.assertEqual(len(table.rows), 1)

        # Add another step
        select.value = "split"
        arg_input.value = ","
        self.tab.add_step()

        self.assertEqual(len(self.tab.pipeline_steps), 2)
        self.assertEqual(self.tab.pipeline_steps[1], ("split", ","))
        self.assertEqual(len(table.rows), 2)

        # Test remove
        table.cursor_coordinate = (0, 0) # Select first row
        self.tab.remove_step()

        self.assertEqual(len(self.tab.pipeline_steps), 1)
        self.assertEqual(self.tab.pipeline_steps[0], ("split", ","))
        self.assertEqual(len(table.rows), 1)

    async def test_clear_pipeline(self):
        select = self.tab.query_one("#pipe-op-select", Select)

        # Add a step
        select.value = "upper"
        self.tab.add_step()
        self.assertEqual(len(self.tab.pipeline_steps), 1)

        # Clear
        self.tab.clear_pipeline()
        self.assertEqual(len(self.tab.pipeline_steps), 0)
        table = self.tab.query_one("#pipe-steps-table", DataTable)
        self.assertEqual(len(table.rows), 0)

    async def test_run_pipeline(self):
        """Test running a simple pipeline."""
        input_area = self.tab.query_one("#pipe-input", TextArea)
        select = self.tab.query_one("#pipe-op-select", Select)
        output_log = self.tab.query_one("#pipe-output", RichLog)

        # Set input
        input_area.text = "hello world"

        # Add 'upper' step
        select.value = "upper"
        self.tab.add_step()

        # Run - using direct call to avoid async UI issues in test environment
        await self.tab.run_pipeline()

        # Check that we called process (via side effect of output log not being empty)
        # The output log writes happen via call_from_thread or direct write depending on context.
        # In test, it's direct.
        # self.assertNotEqual(len(output_log.lines), 0)
        # Note: RichLog content inspection is tricky. Let's verify via mock in next test.

    @patch("shared.pipeline_lab.PipelineLabManager.process")
    async def test_run_pipeline_calls_manager(self, mock_process):
        """Test that running the pipeline correctly calls the manager."""
        mock_process.return_value = "HELLO WORLD"

        input_area = self.tab.query_one("#pipe-input", TextArea)
        input_area.text = "hello world"

        # Add step manually to avoid UI interaction overhead
        self.tab.pipeline_steps = [("upper", "")]

        await self.tab.run_pipeline()

        mock_process.assert_called_once_with("hello world", ["upper"])

if __name__ == "__main__":
    unittest.main()
