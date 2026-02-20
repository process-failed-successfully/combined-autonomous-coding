import unittest
from unittest.mock import patch
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, DataTable, Input
from shared.tui_mock_data import MockDataTab


class MockDataApp(App):
    def compose(self) -> ComposeResult:
        yield MockDataTab(Path("/tmp"))


class TestMockDataTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = MockDataApp()
        self.project_dir = Path("/tmp")

    async def test_add_field(self):
        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(MockDataTab)

            # Input Name
            tab.query_one("#mock-field-name", Input).value = "test_field"

            # Click Add Button via message
            btn = tab.query_one("#btn-mock-add-field", Button)
            btn.post_message(Button.Pressed(btn))

            # Allow event processing
            await pilot.pause()

            # Check schema
            self.assertIn("test_field", tab.schema)
            self.assertEqual(tab.schema["test_field"], "string")

            # Check table
            table = tab.query_one("#mock-schema-table", DataTable)
            self.assertEqual(table.row_count, 1)
            # Use get_cell_at with coordinate tuple
            self.assertEqual(str(table.get_cell_at((0, 0))), "test_field")

    @patch("shared.tui_mock_data.MockDataGenerator")
    async def test_generate(self, MockGenerator):
        # Setup mock
        mock_gen_instance = MockGenerator.return_value
        mock_gen_instance.generate.return_value = [{"col1": "val1"}, {"col1": "val2"}]

        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(MockDataTab)

            # Add a field first
            tab.schema = {"col1": "string"}

            # Click Generate
            btn = tab.query_one("#btn-mock-generate", Button)
            btn.post_message(Button.Pressed(btn))

            await pilot.pause()

            # Verify generator called
            MockGenerator.assert_called_with({"col1": "string"})
            mock_gen_instance.generate.assert_called_with(10)

            # Verify table populated
            table = tab.query_one("#mock-preview-table", DataTable)
            self.assertEqual(table.row_count, 2)
            self.assertEqual(str(table.get_cell_at((0, 0))), "val1")

    @patch("shared.tui_mock_data.MockDataGenerator")
    async def test_export(self, MockGenerator):
        mock_gen_instance = MockGenerator.return_value
        mock_gen_instance.export.return_value = "mock_content"

        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(MockDataTab)
            tab.generated_data = [{"col1": "val1"}]

            # Set Filename
            tab.query_one("#mock-filename", Input).value = "test.json"

            # Mock Path.write_text
            with patch("pathlib.Path.write_text") as mock_write:
                btn = tab.query_one("#btn-mock-export", Button)
                btn.post_message(Button.Pressed(btn))

                await pilot.pause()

                mock_gen_instance.export.assert_called()
                self.assertTrue(mock_write.called)
                args, _ = mock_write.call_args
                self.assertEqual(args[0], "mock_content")

    async def test_remove_field(self):
        async with self.app.run_test() as pilot:
            tab = pilot.app.query_one(MockDataTab)

            # Pre-populate
            tab.schema = {"f1": "string", "f2": "int"}
            table = tab.query_one("#mock-schema-table", DataTable)
            table.add_row("f1", "string", "", key="f1")
            table.add_row("f2", "int", "", key="f2")

            # Select row
            try:
                table.move_cursor(row=0, column=0)
            except TypeError:
                table.move_cursor(0, 0)

            await pilot.pause()

            # Manually trigger button press
            btn = tab.query_one("#btn-mock-remove-field", Button)
            btn.disabled = False
            btn.post_message(Button.Pressed(btn))

            await pilot.pause()

            self.assertNotIn("f1", tab.schema)
            self.assertIn("f2", tab.schema)
            self.assertEqual(table.row_count, 1)
