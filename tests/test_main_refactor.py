import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import argparse
from pathlib import Path
from main import run_refactor
import sys

class TestMainRefactor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.target_file = self.project_dir / "target.py"
        self.target_file.touch()

    def tearDown(self):
        import shutil
        if self.project_dir.exists():
            shutil.rmtree(self.project_dir)

    @patch("shared.refactor.RefactorManager")
    async def test_refactor_command_success(self, MockManager):
        # Setup
        mock_instance = MockManager.return_value
        mock_instance.refactor_file = AsyncMock(return_value={
            "original_content": "old",
            "new_content": "new",
            "diff": "diff",
            "changed": True
        })

        args = argparse.Namespace(
            file=str(self.target_file),
            instruction="Improve it",
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            diff_only=False,
            yes=True # Skip confirmation
        )

        # Expect SystemExit(0)
        with self.assertRaises(SystemExit) as cm:
            await run_refactor(args)
        self.assertEqual(cm.exception.code, 0)

        mock_instance.apply_changes.assert_called_once()

    @patch("shared.refactor.RefactorManager")
    async def test_refactor_command_no_change(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.refactor_file = AsyncMock(return_value={
            "original_content": "old",
            "new_content": "old",
            "diff": "",
            "changed": False
        })

        args = argparse.Namespace(
            file=str(self.target_file),
            instruction="Improve it",
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            diff_only=False,
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            await run_refactor(args)
        self.assertEqual(cm.exception.code, 0)

        mock_instance.apply_changes.assert_not_called()

    @patch("shared.refactor.RefactorManager")
    async def test_refactor_command_diff_only(self, MockManager):
        mock_instance = MockManager.return_value
        mock_instance.refactor_file = AsyncMock(return_value={
            "original_content": "old",
            "new_content": "new",
            "diff": "diff",
            "changed": True
        })

        args = argparse.Namespace(
            file=str(self.target_file),
            instruction="Improve it",
            project_dir=self.project_dir,
            agent="gemini",
            model=None,
            diff_only=True,
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            await run_refactor(args)
        self.assertEqual(cm.exception.code, 0)

        mock_instance.apply_changes.assert_not_called()

if __name__ == '__main__':
    unittest.main()
