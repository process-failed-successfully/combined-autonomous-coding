import unittest
from unittest.mock import patch
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Input, Select

from shared.tui_todos import TodosLabTab


class MockTodosLabApp(App[None]):
    def __init__(self, project_dir: Path):
        super().__init__()
        self.project_dir = project_dir

    def compose(self) -> ComposeResult:
        yield TodosLabTab(self.project_dir)


class TestTodosLabTUI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/mock/project")
        self.app = MockTodosLabApp(self.project_dir)

    async def test_initial_render(self):
        async with self.app.run_test():
            # Check widgets exist
            self.assertIsNotNone(self.app.query_one("#table-todos"))
            self.assertIsNotNone(self.app.query_one("#btn-todos-scan"))
            self.assertIsNotNone(self.app.query_one("#input-todos-search"))
            self.assertIsNotNone(self.app.query_one("#select-todos-tag"))
            self.assertIsNotNone(self.app.query_one("#log-todos-details"))

            table = self.app.query_one("#table-todos", DataTable)
            columns = [col.label.plain for col in table.columns.values()]
            self.assertIn("File", columns)
            self.assertIn("Text", columns)

    @patch('shared.tui_todos.TodoLabManager')
    async def test_scan_and_populate(self, MockManager):
        # Setup mock data
        mock_instance = MockManager.return_value
        mock_instance.get_todos_with_blame.return_value = [
            {"file": "test.py", "line": 10, "tag": "TODO", "text": "Fix this", "author": "Alice", "date": "2023-01-01"},
            {"file": "utils.py", "line": 20, "tag": "FIXME", "text": "Optimize loop", "author": "Bob", "date": "2023-01-02"}
        ]

        async with self.app.run_test() as pilot:
            # Trigger scan
            app.query_one("#btn-todos-scan").press()
        await pilot.pause()
            await pilot.pause()

            # Verify table populated
            table = self.app.query_one("#table-todos", DataTable)
            self.assertEqual(len(table.rows), 2)

            # Check content of first row
            first_row = table.get_row_at(0)
            self.assertEqual(first_row[0], "test.py")
            self.assertEqual(first_row[2], "TODO")

            # Check filtering by tag
            select = self.app.query_one("#select-todos-tag", Select)
            select.value = "FIXME"
            await pilot.pause()

            self.assertEqual(len(table.rows), 1)
            self.assertEqual(table.get_row_at(0)[2], "FIXME")

            # Check search text
            select.value = "ALL"
            search_input = self.app.query_one("#input-todos-search", Input)
            search_input.value = "Optimize"
            await pilot.pause()

            self.assertEqual(len(table.rows), 1)
            self.assertEqual(table.get_row_at(0)[3], "Optimize loop")


if __name__ == '__main__':
    unittest.main()
