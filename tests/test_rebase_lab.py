import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.tui_rebase import RebaseTUI, RebaseEntry, RebaseItem

class TestRebaseLab(unittest.TestCase):
    def test_rebase_entry(self):
        entry = RebaseEntry("pick", "abcdef1", "message", "pick abcdef1 message")
        self.assertEqual(entry.to_line(), "pick abcdef1 message")

        entry.action = "drop"
        self.assertEqual(entry.to_line(), "drop abcdef1 message")

    @patch('shared.tui_rebase.RebaseItem.update_label')
    @patch('shared.tui_rebase.RebaseTUI.load_file')
    def test_rebase_tui_actions(self, mock_load, mock_update_label):
        # Setup TUI with mock file
        mock_path = MagicMock(spec=Path)
        app = RebaseTUI(mock_path)

        # Manually populate entries
        e1 = RebaseEntry("pick", "111", "msg1", "")
        e2 = RebaseEntry("pick", "222", "msg2", "")
        e3 = RebaseEntry("pick", "333", "msg3", "")

        app.entries = [e1, e2, e3]

        # Create items (mock_update_label handles the UI part)
        item1 = RebaseItem(e1)
        item2 = RebaseItem(e2)
        item3 = RebaseItem(e3)

        # Mock ListView
        mock_list = MagicMock()
        mock_list.children = [item1, item2, item3]
        mock_list.index = 1 # Select e2

        # Patch query_one to return our mock list
        app.query_one = MagicMock(return_value=mock_list)

        # Test Cycle Action
        app.action_cycle_action()
        # e2 should change from pick to reword
        self.assertEqual(mock_list.children[1].entry.action, "reword")
        mock_update_label.assert_called()

        app.action_cycle_action()
        self.assertEqual(mock_list.children[1].entry.action, "edit")

        # Test Set Action
        app.action_set_drop()
        self.assertEqual(mock_list.children[1].entry.action, "drop")

        # Test Move Up
        # Reset
        mock_list.index = 1
        app.action_move_line_up()
        mock_list.remove_children.assert_called()
        mock_list.mount.assert_called()

    @patch('shared.tui_rebase.RebaseItem.update_label')
    def test_parser(self, mock_update_label):
        content = """pick 111 msg1
squash 222 msg2
# comment
exec echo hi
"""
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = content

        app = RebaseTUI(mock_path)

        # Mock query_one to return a mock list
        mock_list = MagicMock()
        app.query_one = MagicMock(return_value=mock_list)

        app.load_file()

        self.assertEqual(len(app.entries), 3) # pick, squash, exec
        self.assertEqual(app.entries[0].action, "pick")
        self.assertEqual(app.entries[1].action, "squash")
        self.assertEqual(app.entries[2].action, "exec")

        self.assertEqual(len(app.comments), 1) # comment

    @patch('shared.tui_rebase.RebaseItem.update_label')
    @patch('shared.tui_rebase.RebaseTUI.exit')
    def test_save(self, mock_exit, mock_update_label):
        mock_path = MagicMock(spec=Path)
        app = RebaseTUI(mock_path)

        e1 = RebaseEntry("pick", "111", "msg1", "")
        e2 = RebaseEntry("drop", "222", "msg2", "")

        # Mock list items
        item1 = RebaseItem(e1)
        item2 = RebaseItem(e2)

        mock_list = MagicMock()
        mock_list.children = [item1, item2]
        app.query_one = MagicMock(return_value=mock_list)

        app.action_save_and_exit()

        # Verify write
        mock_path.write_text.assert_called()
        args = mock_path.write_text.call_args[0][0]
        self.assertIn("pick 111 msg1", args)
        self.assertIn("drop 222 msg2", args)

        mock_exit.assert_called_with(result=0)

if __name__ == '__main__':
    unittest.main()
