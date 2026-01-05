import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import shutil
import os
import argparse
from main import run_revert

class TestMainRevert(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = Path("test_revert_project")
        self.test_dir.mkdir()
        os.chdir(self.test_dir)

        # Initialize a git repository
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)

        # Create and commit an initial file
        self.initial_file = Path("initial_file.txt")
        self.initial_file.write_text("This is the initial content.")
        subprocess.run(["git", "add", self.initial_file], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)

    def tearDown(self):
        # Change back to the original directory and remove the temporary directory
        os.chdir("..")
        shutil.rmtree(self.test_dir)

    def test_revert_discards_modifications(self):
        # Modify the initial file
        self.initial_file.write_text("This is modified content.")

        # Run the revert command
        args = argparse.Namespace(project_dir=Path("."), yes=True)
        with self.assertRaises(SystemExit) as cm:
            run_revert(args)
        self.assertEqual(cm.exception.code, 0)

        # Check that the file is reverted
        self.assertEqual(self.initial_file.read_text(), "This is the initial content.")

    def test_revert_discards_new_untracked_files(self):
        # Create a new untracked file
        new_file = Path("new_file.txt")
        new_file.write_text("This is a new file.")

        # Run the revert command
        args = argparse.Namespace(project_dir=Path("."), yes=True)
        with self.assertRaises(SystemExit) as cm:
            run_revert(args)
        self.assertEqual(cm.exception.code, 0)

        # Check that the new file is deleted
        self.assertFalse(new_file.exists())

    def test_revert_discards_new_tracked_files(self):
        # Create a new tracked file
        new_file = Path("new_tracked_file.txt")
        new_file.write_text("This is a new tracked file.")
        subprocess.run(["git", "add", new_file], check=True, capture_output=True)

        # Run the revert command
        args = argparse.Namespace(project_dir=Path("."), yes=True)
        with self.assertRaises(SystemExit) as cm:
            run_revert(args)
        self.assertEqual(cm.exception.code, 0)

        # Check that the new file is deleted
        self.assertFalse(new_file.exists())

    def test_revert_restores_deleted_files(self):
        # Delete the initial file
        self.initial_file.unlink()

        # Run the revert command
        args = argparse.Namespace(project_dir=Path("."), yes=True)
        with self.assertRaises(SystemExit) as cm:
            run_revert(args)
        self.assertEqual(cm.exception.code, 0)

        # Check that the file is restored
        self.assertTrue(self.initial_file.exists())
        self.assertEqual(self.initial_file.read_text(), "This is the initial content.")

    @patch('builtins.input', return_value='n')
    def test_revert_aborts_on_user_cancel(self, mock_input):
        # Modify the initial file
        self.initial_file.write_text("This is modified content.")

        # Run the revert command
        args = argparse.Namespace(project_dir=Path("."), yes=False)
        with self.assertRaises(SystemExit) as cm:
            run_revert(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(self.initial_file.read_text(), "This is modified content.")

if __name__ == '__main__':
    unittest.main()
