import unittest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
from shared.tui_rename import RenameLabTab


class TestRenameLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.tab = RenameLabTab(self.project_dir)

        # Mock manager
        self.tab.manager = MagicMock()
        self.tab.manager.find_files = MagicMock(return_value=[Path("a.txt"), Path("b.py")])
        self.tab.manager.calculate_renames = MagicMock(return_value=[
            (Path("a.txt"), Path("a_new.txt")),
            (Path("b.py"), Path("b_new.py"))
        ])
        self.tab.manager.apply_renames = MagicMock(return_value=True)

        # Mock notify to avoid NoActiveAppError
        self.tab.notify = MagicMock()

    async def test_initial_state(self):
        # Mock query_one
        self.tab.query_one = MagicMock()

        # Test update_preview logic
        await self.tab.update_preview()

        # Verify manager calls
        self.tab.manager.find_files.assert_called()
        self.tab.manager.calculate_renames.assert_called()

        # Verify notification
        self.tab.notify.assert_called()

    async def test_apply_renames(self):
        self.tab.query_one = MagicMock()
        original_renames = [(Path("a.txt"), Path("b.txt"))]
        self.tab.renames = original_renames

        # Mock update_preview to avoid side effects (re-populating list)
        self.tab.update_preview = AsyncMock()

        await self.tab.on_apply()

        # Verify apply was called with original list
        self.tab.manager.apply_renames.assert_called_with(original_renames, dry_run=False)

        # Verify list was cleared (before update_preview would refill it)
        self.assertEqual(self.tab.renames, [])

        # Verify update_preview was called to refresh UI
        self.tab.update_preview.assert_called()
        self.tab.notify.assert_called()


if __name__ == "__main__":
    unittest.main()
