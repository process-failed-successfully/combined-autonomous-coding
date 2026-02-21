import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_cheatsheet import CheatsheetTab
from textual.widgets import ListView, Markdown, Label, Input

class TestTUICheatsheet(unittest.TestCase):
    def test_init(self):
        tab = CheatsheetTab(Path("."))
        self.assertIsInstance(tab, CheatsheetTab)
        self.assertIsNotNone(tab.manager)

    @patch("shared.tui_cheatsheet.CheatsheetManager")
    def test_load_topics(self, MockManager):
        # Setup mock
        mock_manager = MockManager.return_value
        mock_manager.list_topics.return_value = ["git", "python"]

        tab = CheatsheetTab(Path("."))

        # Mock query_one
        mock_list_view = MagicMock(spec=ListView)
        tab.query_one = MagicMock(return_value=mock_list_view)

        # Call method
        tab.load_topics()

        # Verify
        mock_manager.list_topics.assert_called_once()
        mock_list_view.clear.assert_called_once()
        self.assertEqual(mock_list_view.append.call_count, 2)

    @patch("shared.tui_cheatsheet.CheatsheetManager")
    def test_load_content(self, MockManager):
        mock_manager = MockManager.return_value
        mock_manager.get_content.return_value = "# Git Content"

        tab = CheatsheetTab(Path("."))

        mock_markdown = MagicMock(spec=Markdown)
        mock_label = MagicMock(spec=Label)

        # Mock query_one to return different mocks based on selector
        def query_side_effect(selector, type=None):
            if selector == "#cheat-markdown": return mock_markdown
            if selector == "#cheat-header": return mock_label
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        tab.load_content("git")

        mock_manager.get_content.assert_called_with("git")
        mock_markdown.update.assert_called_with("# Git Content")
        mock_label.update.assert_called()
