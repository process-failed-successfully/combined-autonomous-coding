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
import main

class TestArchivesCLI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up a temporary project directory with archives."""
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.archives_base_dir = self.project_dir / ".agent_archives"
        self.archives_base_dir.mkdir()

        # Create some mock archives
        self.archive1_dir = self.archives_base_dir / "snapshot-2023-01-01_10-00-00"
        self.archive1_dir.mkdir()
        (self.archive1_dir / "file1.txt").write_text("content1")
        (self.archive1_dir / "file2.txt").write_text("shared content")

        self.archive2_dir = self.archives_base_dir / "archive-2023-01-02_12-00-00"
        self.archive2_dir.mkdir()
        (self.archive2_dir / "file1.txt").write_text("content2")
        (self.archive2_dir / "another_file.log").write_text("log data")

        # An empty archive
        (self.archives_base_dir / "empty-archive").mkdir()

        # A file in the main project directory for diffing
        (self.project_dir / "file2.txt").write_text("modified shared content")


    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.test_dir)

    async def run_archives_command(self, *args):
        """Helper to run the 'archives' command and capture output."""
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                await main.main()
            output = mock_stdout.getvalue()
        return cm.exception.code, output

    async def test_archives_list(self):
        """Test the 'archives list' command."""
        with patch.object(sys, 'argv', ['main.py', 'archives', 'list', '--project-dir', str(self.project_dir)]):
            exit_code, output = await self.run_archives_command()
        self.assertEqual(exit_code, 0)
        self.assertIn("snapshot-2023-01-01_10-00-00", output)
        self.assertIn("archive-2023-01-02_12-00-00", output)
        self.assertIn("empty-archive", output)
        self.assertIn("file1.txt", output)
        self.assertIn("another_file.log", output)

    async def test_archives_inspect_summary(self):
        """Test inspecting an archive summary."""
        archive_name = "snapshot-2023-01-01_10-00-00"
        with patch.object(sys, 'argv', ['main.py', 'archives', 'inspect', archive_name, '--project-dir', str(self.project_dir)]):
            exit_code, output = await self.run_archives_command()
        self.assertEqual(exit_code, 0)
        self.assertIn(f"--- Inspecting Archive: {archive_name} ---", output)
        self.assertIn("- file1.txt", output)
        self.assertIn("- file2.txt", output)

    async def test_archives_inspect_file(self):
        """Test inspecting a specific file in an archive."""
        archive_name = "archive-2023-01-02_12-00-00"
        file_name = "file1.txt"
        with patch.object(sys, 'argv', ['main.py', 'archives', 'inspect', archive_name, file_name, '--project-dir', str(self.project_dir)]):
            exit_code, output = await self.run_archives_command()
        self.assertEqual(exit_code, 0)
        self.assertIn(f"--- Contents of {file_name} from {archive_name} ---", output)
        self.assertIn("content2", output)
        self.assertNotIn("log data", output)

    async def test_archives_diff_with_changes(self):
        """Test diffing a file with changes."""
        archive_name = "snapshot-2023-01-01_10-00-00"
        file_name = "file2.txt" # This file exists in project dir but with different content
        with patch.object(sys, 'argv', ['main.py', 'archives', 'diff', archive_name, file_name, '--project-dir', str(self.project_dir)]):
            exit_code, output = await self.run_archives_command()
        self.assertEqual(exit_code, 0)
        self.assertIn(f"--- Diff for {file_name} ---", output)
        self.assertIn("--- a/file2.txt (Project Version)", output)
        self.assertIn("+++ b/file2.txt (Archived Version)", output)
        self.assertIn("-modified shared content", output)
        self.assertIn("+shared content", output)

    async def test_archives_diff_new_file(self):
        """Test diffing a file that doesn't exist in the project."""
        archive_name = "snapshot-2023-01-01_10-00-00"
        file_name = "file1.txt" # This file does not exist in project dir
        with patch.object(sys, 'argv', ['main.py', 'archives', 'diff', archive_name, file_name, '--project-dir', str(self.project_dir)]):
            exit_code, output = await self.run_archives_command()
        self.assertEqual(exit_code, 0)
        self.assertIn("(Project Version - File does not exist)", output)
        self.assertIn("+content1", output)

    async def test_archives_restore_by_name_no_conflict(self):
        """Test restoring from a named archive without conflicts."""
        archive_name = "snapshot-2023-01-01_10-00-00"
        (self.project_dir / "file2.txt").unlink() # Remove the conflicting file

        with patch('builtins.input', return_value='y'):
             with patch.object(sys, 'argv', ['main.py', 'archives', 'restore', archive_name, '--project-dir', str(self.project_dir)]):
                exit_code, output = await self.run_archives_command()

        self.assertEqual(exit_code, 0)
        self.assertIn("Restore complete", output)
        self.assertTrue((self.project_dir / "file1.txt").exists())
        self.assertTrue((self.project_dir / "file2.txt").exists())
        self.assertEqual((self.project_dir / "file1.txt").read_text(), "content1")

    async def test_archives_restore_conflict(self):
        """Test that restore fails if there is a file conflict."""
        archive_name = "snapshot-2023-01-01_10-00-00"
        # file2.txt already exists, creating a conflict
        with patch.object(sys, 'argv', ['main.py', 'archives', 'restore', archive_name, '--project-dir', str(self.project_dir), '--yes']):
             exit_code, output = await self.run_archives_command()

        self.assertEqual(exit_code, 1)
        self.assertIn("Error: The following files already exist", output)
        self.assertIn("- file2.txt", output)
        # Ensure no files were restored
        self.assertFalse((self.project_dir / "file1.txt").exists())

    async def test_archives_clear_specific_archive(self):
        """Test clearing a specific archive."""
        archive_name = "snapshot-2023-01-01_10-00-00"
        with patch('builtins.input', return_value='y'):
            with patch.object(sys, 'argv', ['main.py', 'archives', 'clear', archive_name, '--project-dir', str(self.project_dir)]):
                exit_code, output = await self.run_archives_command()

        self.assertEqual(exit_code, 0)
        self.assertIn(f"Archive '{archive_name}' deleted.", output)
        self.assertFalse(self.archive1_dir.exists())
        self.assertTrue(self.archive2_dir.exists()) # Ensure other archive is not deleted

    async def test_archives_clear_all_archives(self):
        """Test clearing all archives with --all."""
        with patch('builtins.input', return_value='y'):
            with patch.object(sys, 'argv', ['main.py', 'archives', 'clear', '--all', '--project-dir', str(self.project_dir)]):
                exit_code, output = await self.run_archives_command()

        self.assertEqual(exit_code, 0)
        self.assertIn("Archives successfully cleared.", output)
        self.assertFalse(self.archives_base_dir.exists())

    async def test_archives_clear_dry_run(self):
        """Test that clear --all --dry-run makes no changes."""
        with patch.object(sys, 'argv', ['main.py', 'archives', 'clear', '--all', '--project-dir', str(self.project_dir), '--dry-run']):
            exit_code, output = await self.run_archives_command()

        self.assertEqual(exit_code, 0)
        self.assertIn("Would permanently delete the entire '.agent_archives' directory", output)
        self.assertTrue(self.archives_base_dir.exists()) # Should still exist
        self.assertTrue(self.archive1_dir.exists())

if __name__ == '__main__':
    unittest.main()
