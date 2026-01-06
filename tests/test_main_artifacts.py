import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path
import tempfile
import shutil
import argparse

# Ensure the main script can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from main import run_artifacts

class TestArtifactsCLI(unittest.TestCase):
    def setUp(self):
        """Set up a temporary project directory with archives and trash."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

        # Create trash and archives directories
        self.trash_base_dir = self.project_dir / ".agent_trash"
        self.trash_base_dir.mkdir()
        self.archives_base_dir = self.project_dir / ".agent_archives"
        self.archives_base_dir.mkdir()

        # --- Create Mock Trash ---
        self.trash1_dir = self.trash_base_dir / "trash-2023-01-01_10-00-00"
        self.trash1_dir.mkdir()
        (self.trash1_dir / "file1.txt").write_text("trash content1")

        self.trash2_dir = self.trash_base_dir / "trash-2023-01-02_12-00-00"
        self.trash2_dir.mkdir()
        (self.trash2_dir / "file2.txt").write_text("trash content2")
        (self.trash2_dir / "shared.txt").write_text("shared trash")

        # --- Create Mock Archives ---
        self.archive1_dir = self.archives_base_dir / "archive-2023-01-03_14-00-00"
        self.archive1_dir.mkdir()
        (self.archive1_dir / "file3.txt").write_text("archive content3")
        (self.archive1_dir / "shared.txt").write_text("shared archive")

        # A file in the main project directory for diffing/conflict tests
        (self.project_dir / "shared.txt").write_text("modified shared content")

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    def run_artifacts_command(self, mode, action, archive_name=None, file_name=None, all_flag=False, yes_flag=True, dry_run_flag=False, input_side_effect=None):
        """Helper to run 'artifacts' commands with a namespace object."""
        args = argparse.Namespace(
            type=mode,
            action=action,
            archive_name=archive_name,
            file_name=file_name,
            project_dir=self.project_dir,
            all=all_flag,
            yes=yes_flag,
            dry_run=dry_run_flag
        )

        with patch('builtins.input', side_effect=input_side_effect or ['']):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
                with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                    with self.assertRaises(SystemExit) as cm:
                        run_artifacts(args, mode=mode)

        return cm.exception.code, mock_stdout.getvalue(), mock_stderr.getvalue()

    def test_list_trash_and_archives(self):
        """Test listing contents of both trash and archives."""
        exit_code, output, _ = self.run_artifacts_command('trash', 'list')
        self.assertEqual(exit_code, 0)
        self.assertIn("--- Trash in:", output)
        self.assertIn("trash-2023-01-02_12-00-00", output)
        self.assertIn("file2.txt", output)

        exit_code, output, _ = self.run_artifacts_command('archive', 'list')
        self.assertEqual(exit_code, 0)
        self.assertIn("--- Archives in:", output)
        self.assertIn("archive-2023-01-03_14-00-00", output)
        self.assertIn("file3.txt", output)

    def test_restore_from_trash(self):
        """Test restoring from trash (should move files)."""
        (self.project_dir / "shared.txt").unlink() # Remove conflict
        exit_code, output, _ = self.run_artifacts_command('trash', 'restore', archive_name="trash-2023-01-02_12-00-00")
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ Restore complete.", output)
        self.assertTrue((self.project_dir / "file2.txt").exists())
        self.assertTrue((self.project_dir / "shared.txt").exists())
        self.assertEqual((self.project_dir / "file2.txt").read_text(), "trash content2")
        self.assertFalse(self.trash2_dir.exists())

    def test_restore_from_archive(self):
        """Test restoring from archives (should copy files)."""
        (self.project_dir / "shared.txt").unlink() # Remove conflict
        exit_code, output, _ = self.run_artifacts_command('archive', 'restore', archive_name="archive-2023-01-03_14-00-00")
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ Restore complete. Original archive remains untouched.", output)
        self.assertTrue((self.project_dir / "file3.txt").exists())
        self.assertTrue((self.project_dir / "shared.txt").exists())
        self.assertEqual((self.project_dir / "file3.txt").read_text(), "archive content3")
        self.assertTrue(self.archive1_dir.exists())

    def test_restore_conflict(self):
        """Test that restore fails if a file conflict exists."""
        exit_code, _, stderr = self.run_artifacts_command('trash', 'restore', archive_name="trash-2023-01-02_12-00-00", yes_flag=True)
        self.assertEqual(exit_code, 1)
        self.assertIn("Error: The following files already exist", stderr)
        self.assertIn("shared.txt", stderr)

    def test_interactive_restore(self):
        """Test interactive restore by selecting an item from a list."""
        (self.project_dir / "shared.txt").unlink()
        exit_code, output, _ = self.run_artifacts_command('trash', 'restore', yes_flag=False, input_side_effect=['2', 'y'])
        self.assertEqual(exit_code, 0)
        self.assertTrue((self.project_dir / "file1.txt").exists())
        self.assertIn("Please select a trash archive to restore", output)
        self.assertIn("[1] trash-2023-01-02_12-00-00", output)
        self.assertIn("[2] trash-2023-01-01_10-00-00", output)

    def test_clear_specific_and_all(self):
        """Test clearing a specific archive and clearing all archives."""
        exit_code, output, _ = self.run_artifacts_command('trash', 'clear', archive_name="trash-2023-01-01_10-00-00")
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ Archive 'trash-2023-01-01_10-00-00' deleted.", output)
        self.assertFalse(self.trash1_dir.exists())

        exit_code, output, _ = self.run_artifacts_command('archive', 'clear', all_flag=True)
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ Archive successfully emptied.", output)
        self.assertFalse(self.archives_base_dir.exists())

    def test_inspect_file_and_summary(self):
        """Test inspecting a specific file and a summary of an archive."""
        exit_code, output, _ = self.run_artifacts_command('trash', 'inspect', archive_name="trash-2023-01-02_12-00-00", file_name="file2.txt")
        self.assertEqual(exit_code, 0)
        self.assertIn("--- Contents of file2.txt", output)
        self.assertIn("trash content2", output)

        exit_code, output, _ = self.run_artifacts_command('archive', 'inspect', archive_name="archive-2023-01-03_14-00-00")
        self.assertEqual(exit_code, 0)
        self.assertIn("--- Inspecting Archive: archive-2023-01-03_14-00-00", output)
        self.assertIn("archive content3", output)

    def test_diff_with_changes(self):
        """Test diffing a file that has been modified."""
        archive_name = "archive-2023-01-03_14-00-00"
        exit_code, output, _ = self.run_artifacts_command('archive', 'diff', archive_name=archive_name, file_name="shared.txt")
        self.assertEqual(exit_code, 0)
        self.assertIn("--- Diff for shared.txt ---", output)
        self.assertIn(f"(Archived Version in {archive_name})", output)
        self.assertIn("-modified shared content", output)
        self.assertIn("+shared archive", output)

    def test_diff_new_file(self):
        """Test diffing a file that only exists in the archive."""
        exit_code, output, _ = self.run_artifacts_command('trash', 'diff', archive_name="trash-2023-01-01_10-00-00", file_name="file1.txt")
        self.assertEqual(exit_code, 0)
        self.assertIn("+trash content1", output)

    def test_diff_no_difference(self):
        """Test diffing a file with no changes."""
        (self.project_dir / "file3.txt").write_text("archive content3")
        exit_code, output, _ = self.run_artifacts_command('archive', 'diff', archive_name="archive-2023-01-03_14-00-00", file_name="file3.txt")
        self.assertEqual(exit_code, 0)
        self.assertIn("✅ No differences found", output)

if __name__ == '__main__':
    unittest.main()
