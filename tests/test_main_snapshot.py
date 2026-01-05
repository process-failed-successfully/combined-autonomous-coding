
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
import shutil
import tempfile
import argparse
import io
from datetime import datetime

# Ensure the script can find the main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_snapshot

class TestSnapshotCommand(unittest.TestCase):

    def setUp(self):
        """Set up a temporary directory and mock project files."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.repo_root = Path(__file__).parent.parent
        self.logs_dir = self.repo_root / "agents/logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Create mock artifacts
        self.mock_artifacts = {
            "feature_list.json": '{"features": []}',
            "qa_summary.txt": "QA summary content.",
            "reviewer_report.txt": "Reviewer report content.",
            ".agent_run_id": "test_run_123"
        }
        for name, content in self.mock_artifacts.items():
            (self.project_dir / name).write_text(content)

        # Create a mock log file
        self.mock_log_file = self.logs_dir / "test_run_123.log"
        self.mock_log_file.write_text("Log file content.")

        self.archive_dir = self.project_dir / ".agent_archives"

        # Mock datetime to control snapshot names
        self.mock_datetime = MagicMock()
        self.mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0, 0)
        self.patcher = patch('datetime.datetime', self.mock_datetime)
        self.patcher.start()

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)
        if self.mock_log_file.exists():
            self.mock_log_file.unlink()
        self.patcher.stop()

    def test_snapshot_creates_timestamped_archive(self):
        """Verify snapshot creates a correctly named archive and copies files."""
        args = argparse.Namespace(
            action='create',
            project_dir=self.project_dir,
            name=None,
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            run_snapshot(args)
        self.assertEqual(cm.exception.code, 0)

        self.assertTrue(self.archive_dir.exists())
        snapshot_dirs = list(self.archive_dir.iterdir())
        self.assertEqual(len(snapshot_dirs), 1)
        snapshot_dir = snapshot_dirs[0]
        self.assertTrue(snapshot_dir.name.startswith("snapshot-"))

        # Verify files were copied
        self.assertTrue((snapshot_dir / "feature_list.json").exists())
        self.assertTrue((snapshot_dir / "qa_summary.txt").exists())
        self.assertTrue((snapshot_dir / "reviewer_report.txt").exists())
        self.assertTrue((snapshot_dir / "test_run_123.log").exists())

        # Verify original files still exist
        self.assertTrue((self.project_dir / "feature_list.json").exists())
        self.assertTrue((self.project_dir / "qa_summary.txt").exists())
        self.assertTrue((self.project_dir / ".agent_run_id").exists())

    def test_snapshot_with_custom_name(self):
        """Verify snapshot works with a user-provided custom name."""
        args = argparse.Namespace(
            action='create',
            project_dir=self.project_dir,
            name="my-custom-snapshot",
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            run_snapshot(args)
        self.assertEqual(cm.exception.code, 0)

        snapshot_dir = self.archive_dir / "my-custom-snapshot"
        self.assertTrue(snapshot_dir.exists())
        self.assertTrue((snapshot_dir / "feature_list.json").exists())

    def test_snapshot_fails_if_archive_exists(self):
        """Verify snapshot exits if a snapshot with the same name already exists."""
        # Create a dummy existing snapshot
        existing_snapshot_dir = self.archive_dir / "my-custom-snapshot"
        existing_snapshot_dir.mkdir(parents=True)

        args = argparse.Namespace(
            action='create',
            project_dir=self.project_dir,
            name="my-custom-snapshot",
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            run_snapshot(args)
        self.assertEqual(cm.exception.code, 1)

    def test_snapshot_no_artifacts(self):
        """Verify snapshot exits gracefully when no artifacts are found."""
        # Clean the directory
        for name in self.mock_artifacts:
            (self.project_dir / name).unlink()
        self.mock_log_file.unlink()

        args = argparse.Namespace(
            action='create',
            project_dir=self.project_dir,
            name=None,
            yes=True
        )

        with self.assertRaises(SystemExit) as cm:
            run_snapshot(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertFalse(self.archive_dir.exists())

    @patch('builtins.input', return_value='y')
    def test_snapshot_interactive_confirmation(self, mock_input):
        """Verify the interactive prompt works correctly."""
        args = argparse.Namespace(
            action='create',
            project_dir=self.project_dir,
            name="interactive-test",
            yes=False
        )
        with self.assertRaises(SystemExit) as cm:
            run_snapshot(args)
        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_called_once()
        self.assertTrue((self.archive_dir / "interactive-test").exists())

    @patch('builtins.input', return_value='n')
    def test_snapshot_interactive_abort(self, mock_input):
        """Verify the interactive prompt aborts correctly."""
        args = argparse.Namespace(
            action='create',
            project_dir=self.project_dir,
            name="interactive-abort-test",
            yes=False
        )
        with self.assertRaises(SystemExit) as cm:
            run_snapshot(args)
        self.assertEqual(cm.exception.code, 0)
        mock_input.assert_called_once()
        self.assertFalse((self.archive_dir / "interactive-abort-test").exists())

    def test_snapshot_diff(self):
        # First, create a snapshot
        create_args = argparse.Namespace(
            action='create',
            name='snapshot-to-diff',
            project_dir=self.project_dir,
            yes=True
        )
        with patch('sys.stdout', new_callable=io.StringIO):
            with self.assertRaises(SystemExit):
                run_snapshot(create_args)

        # Now, modify a file
        (self.project_dir / "feature_list.json").write_text('["feature1", "feature2"]')

        diff_args = argparse.Namespace(
            action='diff',
            name='snapshot-to-diff',
            project_dir=self.project_dir
        )

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_snapshot(diff_args)
            self.assertEqual(cm.exception.code, 0)
            output = mock_stdout.getvalue()
            self.assertIn('feature_list.json', output)
            self.assertIn('--- a', output)
            self.assertIn('+++ b', output)


if __name__ == '__main__':
    unittest.main()
