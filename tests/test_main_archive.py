from main import run_archive
import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import shutil
import io

# Add project root to sys.path to allow importing 'main'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class TestMainArchive(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = Path("./temp_test_dir_for_archive")
        self.test_dir.mkdir(exist_ok=True)

        # Define artifacts to be created for the test
        self.artifacts_to_create = [
            ".agent_db.sqlite",
            "COMPLETED",
            "feature_list.json",
            "worktrees/",
        ]

        # Create dummy artifact files and directories
        for artifact in self.artifacts_to_create:
            path = self.test_dir / artifact
            if artifact.endswith('/'):
                path.mkdir(exist_ok=True)
                (path / "dummy.txt").touch()  # ensure it's not empty
            else:
                path.touch()

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_archive_moves_artifacts(self, mock_stdout):
        """
        Test that `run_archive` correctly identifies and moves artifacts
        to a timestamped directory.
        """
        # Mock args for the function
        args = MagicMock()
        args.project_dir = self.test_dir

        # Run the archive function
        with self.assertRaises(SystemExit) as cm:
            run_archive(args)

        # Check that the function exited cleanly
        self.assertEqual(cm.exception.code, 0)

        # --- Verification ---

        # 1. Verify that the original artifacts are gone
        for artifact in self.artifacts_to_create:
            self.assertFalse((self.test_dir / artifact).exists(), f"Artifact '{artifact}' should have been moved.")

        # 2. Verify that an archive directory was created
        archive_base_dir = self.test_dir / ".agent_archives"
        self.assertTrue(archive_base_dir.exists())

        # There should be exactly one archive sub-directory
        archive_dirs = list(archive_base_dir.iterdir())
        self.assertEqual(len(archive_dirs), 1)

        archive_dir = archive_dirs[0]
        self.assertTrue(archive_dir.is_dir())
        self.assertTrue(archive_dir.name.startswith("archive-"))

        # 3. Verify that the artifacts now exist in the archive directory
        for artifact in self.artifacts_to_create:
            archived_path = archive_dir / Path(artifact).name
            self.assertTrue(archived_path.exists(), f"Artifact '{artifact}' should exist in the archive directory.")

        # 4. Check stdout for confirmation message
        output = mock_stdout.getvalue()
        self.assertIn("Archiving complete.", output)
        self.assertIn(str(archive_dir.relative_to(self.test_dir)), output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_archive_no_artifacts(self, mock_stdout):
        """
        Test that `run_archive` does nothing when no artifacts are present.
        """
        # A fresh directory with no artifacts
        empty_dir = self.test_dir / "empty"
        empty_dir.mkdir()

        args = MagicMock()
        args.project_dir = empty_dir

        with self.assertRaises(SystemExit) as cm:
            run_archive(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify no archive directory was created
        self.assertFalse((empty_dir / ".agent_archives").exists())

        # Verify the output message
        self.assertIn("No agent-generated artifacts found to archive.", mock_stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
