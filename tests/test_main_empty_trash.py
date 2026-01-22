from main import run_empty_trash
import unittest
from unittest.mock import patch
import sys
import os
from pathlib import Path
import shutil
import io
import argparse

# Ensure the main module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestEmptyTrash(unittest.TestCase):

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

        # Redirect stdout to capture print statements
        self.stdout_capture = io.StringIO()
        sys.stdout = self.stdout_capture

    def tearDown(self):
        """Clean up the temporary directory and restore stdout."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        sys.stdout = sys.__stdout__

    def _create_mock_input(self, return_value):
        """Helper to create a mock for builtins.input that also prints the prompt."""
        def mock_input(prompt):
            print(prompt, end="")
            return return_value
        return mock_input

    def test_empty_trash_with_yes_flag(self):
        """Test that trash is emptied when --yes is provided."""
        args = argparse.Namespace(project_dir=self.test_dir, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_empty_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.trash_dir.exists())
        output = self.stdout_capture.getvalue()
        self.assertIn("Permanently emptying trash", output)
        self.assertIn("Trash successfully emptied", output)

    def test_empty_trash_with_user_confirmation_yes(self):
        """Test that trash is emptied when user confirms with 'y'."""
        args = argparse.Namespace(project_dir=self.test_dir, yes=False)

        mock_input_y = self._create_mock_input('y')
        with patch('builtins.input', side_effect=mock_input_y) as mock_input_call:
            with self.assertRaises(SystemExit) as cm:
                run_empty_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.trash_dir.exists())
        output = self.stdout_capture.getvalue()
        self.assertIn("Are you sure you want to proceed? [y/N]:", output)

    def test_empty_trash_with_user_confirmation_no(self):
        """Test that trash is NOT emptied when user confirms with 'n'."""
        args = argparse.Namespace(project_dir=self.test_dir, yes=False)

        mock_input_n = self._create_mock_input('n')
        with patch('builtins.input', side_effect=mock_input_n):
            with self.assertRaises(SystemExit) as cm:
                run_empty_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertTrue(self.trash_dir.exists())  # Should still exist
        output = self.stdout_capture.getvalue()
        self.assertIn("Are you sure you want to proceed? [y/N]:", output)
        self.assertIn("Aborted.", output)

    def test_empty_trash_when_no_trash_directory_exists(self):
        """Test the command when the trash directory does not exist."""
        shutil.rmtree(self.trash_dir)  # Remove it first
        args = argparse.Namespace(project_dir=self.test_dir, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_empty_trash(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("Trash directory (.agent_trash) not found.", self.stdout_capture.getvalue())

    def test_empty_trash_when_trash_is_already_empty(self):
        """Test the command when the trash directory is empty."""
        # Clear the trash directory contents
        for item in self.trash_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

        args = argparse.Namespace(project_dir=self.test_dir, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_empty_trash(args)

        self.assertEqual(cm.exception.code, 0)
        # The function should also remove the now-empty .agent_trash directory
        self.assertFalse(self.trash_dir.exists())
        output = self.stdout_capture.getvalue()
        self.assertIn("Trash directory is already empty.", output)
        self.assertIn("Removed empty .agent_trash directory.", output)


if __name__ == '__main__':
    unittest.main()
