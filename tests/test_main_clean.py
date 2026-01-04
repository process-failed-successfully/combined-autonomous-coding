import unittest
from unittest.mock import patch
import sys
import os
from pathlib import Path
import shutil
import tempfile
import io
from contextlib import redirect_stdout
import argparse

# Ensure the main script can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_clean

class TestMainCleanCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory with mock artifacts and user files."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)

        # Agent-generated files and directories
        self.agent_artifacts = [
            ".agent_db.sqlite",
            "COMPLETED",
            "QA_PASSED",
            "PROJECT_SIGNED_OFF",
            "feature_list.json",
            "qa_summary.txt",
            "reviewer_report.txt",
            "cleanup_report.txt",
            "final_metrics.txt",
            "temp_files.txt",
            "dashboard_state.json",
            "worktrees/",
        ]

        # User-generated files that should NOT be deleted
        self.user_files = [
            "app.py",
            "README.md",
            "src/component.js",
            "src/styles.css",
        ]

        # Create all mock files and directories
        for artifact in self.agent_artifacts:
            path = self.project_path / artifact
            if artifact.endswith('/'):
                path.mkdir(parents=True, exist_ok=True)
                (path / "test.file").touch() # ensure directory is not empty
            else:
                path.touch()

        for user_file in self.user_files:
            path = self.project_path / user_file
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    def tearDown(self):
        """Remove the temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_clean_moves_artifacts_to_trash_by_default(self):
        """Verify that artifacts are moved to a trash directory by default."""
        args = argparse.Namespace(project_dir=self.project_path, yes=True, force=False)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        for artifact in self.agent_artifacts:
            self.assertFalse((self.project_path / artifact).exists(), f"{artifact} should have been moved")

        for user_file in self.user_files:
            self.assertTrue((self.project_path / user_file).exists(), f"{user_file} should NOT have been touched")

        trash_dir = self.project_path / ".agent_trash"
        self.assertTrue(trash_dir.is_dir())

        trash_contents = list(trash_dir.iterdir())
        self.assertEqual(len(trash_contents), 1)
        timestamped_trash_dir = trash_contents[0]
        self.assertTrue(timestamped_trash_dir.is_dir())

        for artifact in self.agent_artifacts:
            artifact_name = Path(artifact).name
            self.assertTrue((timestamped_trash_dir / artifact_name).exists(), f"{artifact_name} should be in the trash directory")

    def test_clean_with_force_removes_agent_artifacts_only(self):
        """Verify that --force permanently deletes only agent-generated files."""
        args = argparse.Namespace(project_dir=self.project_path, yes=True, force=True)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        for artifact in self.agent_artifacts:
            self.assertFalse((self.project_path / artifact).exists(), f"{artifact} should have been deleted")

        for user_file in self.user_files:
            self.assertTrue((self.project_path / user_file).exists(), f"{user_file} should NOT have been deleted")

        self.assertFalse((self.project_path / ".agent_trash").exists())

    @patch('builtins.input', return_value='y')
    def test_clean_with_user_confirmation_yes_moves_to_trash(self, mock_input):
        """Test the interactive 'yes' confirmation moves artifacts to trash."""
        args = argparse.Namespace(project_dir=self.project_path, yes=False, force=False)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'):
                run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        mock_input.assert_called_once()
        self.assertFalse((self.project_path / "COMPLETED").exists(), "File should be moved after 'y' confirmation")
        self.assertTrue((self.project_path / ".agent_trash").exists())

    @patch('builtins.input', return_value='n')
    def test_clean_with_user_confirmation_no_aborts(self, mock_input):
        """Test the interactive 'no' confirmation aborts the operation."""
        args = argparse.Namespace(project_dir=self.project_path, yes=False, force=False)

        with patch('sys.stdout'), self.assertRaises(SystemExit) as cm:
            run_clean(args)

        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_called_once()
        self.assertTrue((self.project_path / "COMPLETED").exists(), "File should NOT be moved after 'n' confirmation")
        self.assertFalse((self.project_path / ".agent_trash").exists())

    def test_clean_with_yes_flag_skips_confirmation_and_moves_to_trash(self):
        """Test that -y skips confirmation and moves artifacts to trash."""
        args = argparse.Namespace(project_dir=self.project_path, yes=True, force=False)

        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stdout'), patch('builtins.input') as mock_input:
                run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        mock_input.assert_not_called()
        self.assertFalse((self.project_path / "COMPLETED").exists(), "File should be moved without confirmation")
        self.assertTrue((self.project_path / ".agent_trash").exists())

    def test_clean_on_directory_with_no_artifacts(self):
        """Test clean command on a directory with no agent artifacts."""
        clean_dir = Path(tempfile.mkdtemp())
        args = argparse.Namespace(project_dir=clean_dir, yes=True, force=False)

        f = io.StringIO()
        with redirect_stdout(f), self.assertRaises(SystemExit) as cm:
            run_clean(args)

        self.assertEqual(cm.exception.code, 0)
        output = f.getvalue()
        self.assertIn("No agent-generated artifacts found to clean", output)

        shutil.rmtree(clean_dir)

if __name__ == '__main__':
    unittest.main()
