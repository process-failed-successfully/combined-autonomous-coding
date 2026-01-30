import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_conflict import ConflictTab

class TestTUIConflict(unittest.TestCase):
    @patch("shared.tui_conflict.ConflictResolver")
    def test_conflict_tab_init(self, mock_resolver_cls):
        mock_resolver = MagicMock()
        mock_resolver_cls.return_value = mock_resolver

        tab = ConflictTab(Path("."))

        # Check initial state
        self.assertEqual(tab.conflicted_files, [])
        self.assertIsNone(tab.selected_file)

        # Verify resolver initialized
        mock_resolver_cls.assert_called_once_with(Path("."))

    @patch("shared.tui_conflict.ConflictResolver")
    def test_refresh_list(self, mock_resolver_cls):
        mock_resolver = MagicMock()
        mock_resolver_cls.return_value = mock_resolver

        # Mock finding files
        mock_resolver.find_conflicted_files.return_value = [Path("conflict1.py"), Path("conflict2.py")]

        tab = ConflictTab(Path("."))

        # Mock TUI query methods since we are not running a full app
        mock_list_view = MagicMock()
        mock_log = MagicMock()
        mock_counter = MagicMock()

        def query_side_effect(selector, type=None):
            if selector == "#conflict-file-list": return mock_list_view
            if selector == "#conflict-view": return mock_log
            if selector == "#lbl-conflict-counter": return mock_counter
            return MagicMock()

        tab.query_one = MagicMock(side_effect=query_side_effect)

        # Run refresh
        tab.refresh_list()

        # Verify find called
        mock_resolver.find_conflicted_files.assert_called_once()

        # Verify list updated (clear called, then append called 2 times)
        mock_list_view.clear.assert_called_once()
        self.assertEqual(mock_list_view.append.call_count, 2)

if __name__ == "__main__":
    unittest.main()
