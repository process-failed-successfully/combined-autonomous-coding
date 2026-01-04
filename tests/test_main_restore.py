import unittest
from unittest.mock import patch
import sys
import os
from pathlib import Path
import shutil
import tempfile
import argparse
import io
from contextlib import redirect_stdout

# Ensure the main script can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_clean, run_restore

class TestMainRestoreCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory with mock artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)

        self.agent_artifacts = [
            ".agent_db.sqlite",
            "COMPLETED",
            "feature_list.json",
            "worktrees/",
        ]

        for artifact in self.agent_artifacts:
            path = self.project_path / artifact
            if artifact.endswith('/'):
                path.mkdir(parents=True, exist_ok=True)
                (path / "test.file").touch()
            else:
                path.touch()

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def _run_clean(self):
        """Helper to run the clean command and create a trash directory."""
        args = argparse.Namespace(project_dir=self.project_path, yes=True, force=False, archive=False)
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_clean(args)
        self.assertEqual(cm.exception.code, 0)

    def test_restore_restores_artifacts_from_trash(self):
        """Verify that restore moves artifacts from the trash back to the project directory."""
        self._run_clean()

        # Verify artifacts are gone from project root
        for artifact in self.agent_artifacts:
            self.assertFalse((self.project_path / artifact).exists())

        # Now, run restore
        args = argparse.Namespace(project_dir=self.project_path, yes=True)
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_restore(args)
        self.assertEqual(cm.exception.code, 0)

        # Verify artifacts are back
        for artifact in self.agent_artifacts:
            self.assertTrue((self.project_path / artifact).exists())

        # Verify trash directory is empty or removed
        trash_dir = self.project_path / ".agent_trash"
        self.assertFalse(any(trash_dir.iterdir()), ".agent_trash should be empty")


    def test_restore_aborts_if_conflicting_files_exist(self):
        """Verify that restore aborts if a file to be restored already exists."""
        self._run_clean()

        # Re-create one of the trashed files in the project directory
        (self.project_path / "COMPLETED").touch()

        args = argparse.Namespace(project_dir=self.project_path, yes=True)
        with self.assertRaises(SystemExit) as cm:
             with patch('sys.stderr'):
                run_restore(args)
        self.assertEqual(cm.exception.code, 1)

    @patch('builtins.input', return_value='n')
    def test_restore_with_user_confirmation_no_aborts(self, mock_input):
        """Test the interactive 'no' confirmation aborts the restore operation."""
        self._run_clean()

        args = argparse.Namespace(project_dir=self.project_path, yes=False)

        with patch('sys.stdout'), self.assertRaises(SystemExit) as cm:
            run_restore(args)

        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_called_once()
        self.assertFalse((self.project_path / "COMPLETED").exists(), "File should NOT be restored after 'n' confirmation")

if __name__ == '__main__':
    unittest.main()
