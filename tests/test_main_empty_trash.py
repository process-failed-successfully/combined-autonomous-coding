import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
import shutil
import io
import argparse

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_trash

class TestTrashClear(unittest.TestCase):

    def setUp(self):
        """Set up a temporary project directory with a trash folder."""
        self.test_dir = Path("./test_project_temp")
        self.test_dir.mkdir(exist_ok=True)

        self.trash_dir = self.test_dir / ".agent_trash"
        self.trash_dir.mkdir(exist_ok=True)

        # Create some dummy files and directories in the trash
        (self.trash_dir / "trash-2023-01-01_12-00-00").mkdir()
        (self.trash_dir / "trash-2023-01-01_12-00-00" / "some_file.txt").touch()
        (self.trash_dir / "trash-2023-01-02_12-00-00").mkdir()

    def tearDown(self):
        """Clean up the temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_trash_clear_with_yes_flag(self):
        """Test that trash is cleared when --yes and --all are provided."""
        args = argparse.Namespace(
            command='trash',
            action='clear',
            project_dir=self.test_dir,
            archive_name=None,
            all=True,
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
             with patch('sys.stdout'):
                run_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.trash_dir.exists())

    @patch('builtins.input', return_value='y')
    def test_trash_clear_with_user_confirmation_yes(self, mock_input):
        """Test that trash is cleared when user confirms with 'y'."""
        args = argparse.Namespace(
            command='trash',
            action='clear',
            project_dir=self.test_dir,
            archive_name=None,
            all=True,
            yes=False
        )
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.trash_dir.exists())
        mock_input.assert_called_once()

    @patch('builtins.input', return_value='n')
    def test_trash_clear_with_user_confirmation_no(self, mock_input):
        """Test that trash is NOT cleared when user confirms with 'n'."""
        args = argparse.Namespace(
            command='trash',
            action='clear',
            project_dir=self.test_dir,
            archive_name=None,
            all=True,
            yes=False
        )

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(self.trash_dir.exists())
        mock_input.assert_called_once()

    def test_trash_clear_when_no_trash_directory_exists(self):
        """Test the command when the trash directory does not exist."""
        shutil.rmtree(self.trash_dir) # Remove it first
        args = argparse.Namespace(
            command='trash',
            action='clear',
            project_dir=self.test_dir,
            archive_name=None,
            all=True,
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_trash(args)

        self.assertEqual(cm.exception.code, 0)

if __name__ == '__main__':
    unittest.main()
