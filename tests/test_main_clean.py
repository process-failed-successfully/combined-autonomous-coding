from main import run_clean
import unittest
from unittest.mock import patch
import shutil
from pathlib import Path
import argparse
import sys
import io
from contextlib import redirect_stdout

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class TestMainClean(unittest.TestCase):

    def setUp(self):
        """Set up a temporary test directory."""
        self.test_dir = Path("./test_project_temp").resolve()
        self.test_dir.mkdir(exist_ok=True)

        self.agent_artifacts = [
            ".agent_db.sqlite", "COMPLETED", "feature_list.json", "worktrees/"
        ]
        self.user_file = "user_file.txt"

        # Create dummy artifacts and a user file
        for artifact in self.agent_artifacts:
            path = self.test_dir / artifact
            if artifact.endswith('/'):
                path.mkdir(parents=True, exist_ok=True)
                (path / "dummy_file.txt").touch()
            else:
                path.touch()
        (self.test_dir / self.user_file).touch()

    def tearDown(self):
        """Clean up the test directory."""
        shutil.rmtree(self.test_dir)

    def test_clean_default_trash_mode(self):
        """Test the default 'clean' command moves artifacts to .agent_trash."""
        args = argparse.Namespace(project_dir=self.test_dir, force=False, archive=False, list=False, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        trash_base_dir = self.test_dir / ".agent_trash"
        self.assertTrue(trash_base_dir.exists())
        trashed_items = list(trash_base_dir.iterdir())
        self.assertEqual(len(trashed_items), 1)
        trash_dir = trashed_items[0]
        self.assertTrue(trash_dir.name.startswith("trash-"))

        for artifact in self.agent_artifacts:
            self.assertTrue((trash_dir / artifact.strip('/')).exists())
            self.assertFalse((self.test_dir / artifact.strip('/')).exists())

        self.assertTrue((self.test_dir / self.user_file).exists())

    def test_clean_force_delete_mode(self):
        """Test 'clean --force' permanently deletes artifacts."""
        args = argparse.Namespace(project_dir=self.test_dir, force=True, archive=False, list=False, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        for artifact in self.agent_artifacts:
            self.assertFalse((self.test_dir / artifact.strip('/')).exists())

        self.assertFalse((self.test_dir / ".agent_trash").exists())
        self.assertFalse((self.test_dir / ".agent_archives").exists())
        self.assertTrue((self.test_dir / self.user_file).exists())

    def test_clean_archive_mode(self):
        """Test 'clean --archive' moves artifacts to .agent_archives."""
        args = argparse.Namespace(project_dir=self.test_dir, force=False, archive=True, list=False, yes=True)

        with self.assertRaises(SystemExit) as cm:
            run_clean(args)
        self.assertEqual(cm.exception.code, 0)

        archive_base_dir = self.test_dir / ".agent_archives"
        self.assertTrue(archive_base_dir.exists())
        archive_dirs = list(archive_base_dir.iterdir())
        self.assertEqual(len(archive_dirs), 1)
        archive_dir = archive_dirs[0]
        self.assertTrue(archive_dir.name.startswith("archive-"))

        for artifact in self.agent_artifacts:
            self.assertTrue((archive_dir / artifact.strip('/')).exists())
            self.assertFalse((self.test_dir / artifact.strip('/')).exists())

        self.assertFalse((self.test_dir / ".agent_trash").exists())
        self.assertTrue((self.test_dir / self.user_file).exists())

    def test_no_artifacts_to_clean(self):
        """Test clean command exits gracefully when no artifacts are found."""
        # Remove artifacts created in setUp
        for artifact in self.agent_artifacts:
            path = self.test_dir / artifact
            if path.is_dir():
                shutil.rmtree(path)
            elif path.is_file():
                path.unlink()

        args = argparse.Namespace(project_dir=self.test_dir, force=False, archive=False, list=False, yes=True)

        f = io.StringIO()
        with redirect_stdout(f), self.assertRaises(SystemExit) as cm:
            run_clean(args)

        self.assertEqual(cm.exception.code, 0)
        self.assertIn("No agent-generated artifacts found to clean", f.getvalue())

    @patch('builtins.input', return_value='y')
    def test_interactive_confirm_yes(self, mock_input):
        """Test interactive confirmation 'y' proceeds with cleaning."""
        args = argparse.Namespace(project_dir=self.test_dir, force=False, archive=False, list=False, yes=False)
        with self.assertRaises(SystemExit):
            run_clean(args)

        mock_input.assert_called_once()
        self.assertTrue((self.test_dir / ".agent_trash").exists())

    @patch('builtins.input', return_value='n')
    def test_interactive_confirm_no(self, mock_input):
        """Test interactive confirmation 'n' aborts the cleaning."""
        args = argparse.Namespace(project_dir=self.test_dir, force=False, archive=False, list=False, yes=False)
        with self.assertRaises(SystemExit) as cm:
            run_clean(args)

        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_called_once()
        self.assertFalse((self.test_dir / ".agent_trash").exists())
        self.assertTrue((self.test_dir / "COMPLETED").exists())

    def test_clean_includes_agent_log(self):
        """Test that the agent log file is included in the cleaned artifacts."""
        mock_repo_root = self.test_dir / "repo"
        mock_repo_root.mkdir(exist_ok=True)
        mock_main_py_path = str(mock_repo_root / "main.py")

        with patch('main.__file__', mock_main_py_path):
            # Create a mock log file relative to our mocked repo root
            log_dir = mock_repo_root / "agents/logs"
            log_dir.mkdir(parents=True)
            run_id = "test_run_123"
            log_file = log_dir / f"{run_id}.log"
            log_file.write_text("This is a test log.")

            # Create the .agent_run_id file in the project dir
            (self.test_dir / ".agent_run_id").write_text(run_id)

            args = argparse.Namespace(project_dir=self.test_dir, force=False, archive=False, list=False, yes=True)

            with self.assertRaises(SystemExit) as cm:
                run_clean(args)
            self.assertEqual(cm.exception.code, 0)

            trash_base_dir = self.test_dir / ".agent_trash"
            self.assertTrue(trash_base_dir.exists())
            trash_dir = list(trash_base_dir.iterdir())[0]

            # Verify log file was moved
            self.assertTrue((trash_dir / f"{run_id}.log").exists())
            self.assertFalse(log_file.exists())


if __name__ == '__main__':
    unittest.main()
