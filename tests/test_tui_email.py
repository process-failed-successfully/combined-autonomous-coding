import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from textual.widgets import DataTable
from shared.tui_email import EmailLabTab

class TestEmailLabTab(unittest.TestCase):
    def test_instantiation(self):
        with patch("shared.tui_email.EmailLabManager") as MockManager:
            tab = EmailLabTab(Path("/tmp"))
            self.assertIsInstance(tab, EmailLabTab)
            self.assertIsNotNone(tab.manager)

    def test_compose(self):
        with patch("shared.tui_email.EmailLabManager"):
            tab = EmailLabTab(Path("/tmp"))
            self.assertTrue(hasattr(tab, "compose"))

    def test_refresh_inbox_populates_table(self):
        # Mock manager
        mock_manager = MagicMock()
        mock_manager.get_emails.return_value = [
            {"id": "1", "timestamp": "2023-01-01", "sender": "a", "recipients": ["b"], "subject": "Test1"},
            {"id": "2", "timestamp": "2023-01-02", "sender": "c", "recipients": ["d"], "subject": "Test2"},
        ]

        with patch("shared.tui_email.EmailLabManager", return_value=mock_manager):
            tab = EmailLabTab(Path("/tmp"))

            # Mock DataTable widget
            mock_table = MagicMock(spec=DataTable)

            # Mock query_one to return our mock table
            tab.query_one = MagicMock(return_value=mock_table)

            # Call refresh
            tab.refresh_inbox()

            # Verify get_emails called
            mock_manager.get_emails.assert_called_with(limit=50)

            # Verify table cleared
            mock_table.clear.assert_called_once()

            # Verify rows added (2 rows)
            self.assertEqual(mock_table.add_row.call_count, 2)

            # Check args of last call (Test2 should be first if reversed? Logic says reversed(emails))
            # get_emails returns [1, 2]. reversed is [2, 1].
            # So first add_row should be 2.
            args, kwargs = mock_table.add_row.call_args_list[0]
            self.assertEqual(args[0], "2") # ID
            self.assertEqual(args[4], "Test2") # Subject

if __name__ == "__main__":
    unittest.main()
