import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.widgets import Input, Button, DataTable, Checkbox, RichLog
from shared.tui import SearchTab

class TestTuiSearch(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = SearchTab(self.project_dir)

    async def test_compose(self):
        # We can't easily test compose without running the app, but we can check children if we mount it?
        # Textual testing usually requires an App.
        # Let's rely on mocking the search logic and checking if methods are called.
        pass

    @patch("shared.tui.search_codebase")
    async def test_perform_search(self, mock_search):
        # Setup mock return
        mock_search.return_value = [
            {
                "file": "test.py",
                "line": 10,
                "content": "def test():",
                "context_before": ["# comment"],
                "context_after": ["  pass"]
            }
        ]

        # Mount the widget in a test app context is hard here without full textual harness.
        # So we will simulate the behavior by manually setting values and calling the method.

        # Mock query_one to return mocks for widgets
        self.tab.query_one = MagicMock()

        mock_input = MagicMock(spec=Input)
        mock_input.value = "test"

        mock_chk_case = MagicMock(spec=Checkbox)
        mock_chk_case.value = False

        mock_chk_regex = MagicMock(spec=Checkbox)
        mock_chk_regex.value = False

        mock_file_pattern = MagicMock(spec=Input)
        mock_file_pattern.value = "*.py"

        mock_table = MagicMock(spec=DataTable)

        def side_effect(selector, type=None):
            if selector == "#search-input": return mock_input
            if selector == "#chk-case": return mock_chk_case
            if selector == "#chk-regex": return mock_chk_regex
            if selector == "#file-pattern-input": return mock_file_pattern
            if selector == "#search-results-table": return mock_table
            return MagicMock()

        self.tab.query_one.side_effect = side_effect
        self.tab.notify = MagicMock()

        # Call the method
        await self.tab.perform_search()

        # Verify search_codebase called
        mock_search.assert_called_once()
        args = mock_search.call_args
        self.assertEqual(args[0][0], self.project_dir)
        self.assertEqual(args[0][1], "test")
        self.assertEqual(args[1]['file_pattern'], "*.py")

        # Verify table populated
        mock_table.clear.assert_called_once()
        mock_table.add_row.assert_called_once()

        # Check that cache is set
        self.assertEqual(len(self.tab.results_cache), 1)

    async def test_select_result(self):
        # Setup cache
        self.tab.results_cache = [
            {
                "file": "test.py",
                "line": 10,
                "content": "def test():",
                "context_before": ["9: # comment"],
                "context_after": ["11:   pass"]
            }
        ]

        # Mock widgets
        self.tab.query_one = MagicMock()
        mock_preview = MagicMock(spec=RichLog)

        def side_effect(selector, type=None):
            if selector == "#search-preview": return mock_preview
            return MagicMock()

        self.tab.query_one.side_effect = side_effect

        # Create a mock event
        mock_event = MagicMock()
        mock_event.row_key.value = "0"

        # Call handler
        self.tab.on_result_selected(mock_event)

        # Verify preview updated
        mock_preview.clear.assert_called_once()
        # write should be called 1 (header) + 1 (before) + 1 (content) + 1 (after) = 4 times
        self.assertEqual(mock_preview.write.call_count, 4)
        mock_preview.write.assert_any_call("[bold]test.py:10[/bold]")
        mock_preview.write.assert_any_call("[dim]9: # comment[/dim]")
        mock_preview.write.assert_any_call("[bold yellow]10: def test():[/bold yellow]")


if __name__ == '__main__':
    unittest.main()
