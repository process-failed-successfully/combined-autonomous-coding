import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from textual.widgets import Input, Button, Checkbox, RichLog
from shared.tui import SearchTab
from rich.syntax import Syntax

class TestTuiReplace(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = SearchTab(self.project_dir)

        # Mock widgets
        self.tab.query_one = MagicMock()

        self.mock_input_search = MagicMock(spec=Input)
        self.mock_input_search.value = "foo"

        self.mock_input_replace = MagicMock(spec=Input)
        self.mock_input_replace.value = "bar"

        self.mock_chk_case = MagicMock(spec=Checkbox)
        self.mock_chk_case.value = False

        self.mock_chk_regex = MagicMock(spec=Checkbox)
        self.mock_chk_regex.value = False

        self.mock_file_pattern = MagicMock(spec=Input)
        self.mock_file_pattern.value = "*.py"

        self.mock_btn_apply = MagicMock(spec=Button)

        self.mock_preview_log = MagicMock(spec=RichLog)

        def side_effect(selector, type=None):
            if selector == "#search-input": return self.mock_input_search
            if selector == "#replace-input": return self.mock_input_replace
            if selector == "#chk-case": return self.mock_chk_case
            if selector == "#chk-regex": return self.mock_chk_regex
            if selector == "#file-pattern-input": return self.mock_file_pattern
            if selector == "#btn-apply-replace": return self.mock_btn_apply
            if selector == "#search-preview": return self.mock_preview_log
            return MagicMock()

        self.tab.query_one.side_effect = side_effect
        self.tab.notify = MagicMock()

        # Mock perform_search to avoid real execution during apply
        self.tab.perform_search = AsyncMock()

    @patch("shared.tui.replace_in_codebase")
    async def test_preview_replace(self, mock_replace):
        # Setup mock return
        mock_replace.return_value = {
            "files_matched": 1,
            "files_changed": 1,
            "replacements_count": 1,
            "diffs": {"test.py": "diff content"}
        }

        # Call the method
        await self.tab.preview_replace()

        # Verify replace_in_codebase called with dry_run=True
        mock_replace.assert_called_once()
        call_args = mock_replace.call_args
        # Positional: project_dir, pattern, replacement
        self.assertEqual(call_args[0][1], "foo")
        self.assertEqual(call_args[0][2], "bar")
        # Keyword: dry_run=True
        self.assertTrue(call_args[1]['dry_run'])

        # Verify preview updated
        self.mock_preview_log.clear.assert_called_once()
        self.mock_preview_log.write.assert_any_call("[bold]Preview Replace: foo -> bar[/bold]")

        # Verify Syntax object was written
        # We check if any call arg was a Syntax object
        found_syntax = False
        for call in self.mock_preview_log.write.call_args_list:
            arg = call[0][0]
            if isinstance(arg, Syntax):
                if arg.code == "diff content":
                    found_syntax = True
        self.assertTrue(found_syntax, "Syntax object with diff content not found in log calls")

        # Verify apply button enabled
        self.assertEqual(self.mock_btn_apply.disabled, False)

    @patch("shared.tui.replace_in_codebase")
    async def test_apply_replace(self, mock_replace):
        # Setup mock return
        mock_replace.return_value = {
            "files_matched": 1,
            "files_changed": 1,
            "replacements_count": 1,
            "diffs": {}
        }

        # Call the method
        await self.tab.apply_replace()

        # Verify replace_in_codebase called with dry_run=False
        mock_replace.assert_called_once()
        call_args = mock_replace.call_args
        self.assertFalse(call_args[1]['dry_run'])

        # Verify notify called
        self.tab.notify.assert_called_with("Replaced 1 occurrences in 1 files.")

        # Verify apply button disabled
        self.assertEqual(self.mock_btn_apply.disabled, True)

        # Verify search refreshed
        self.tab.perform_search.assert_called_once()

if __name__ == '__main__':
    unittest.main()
