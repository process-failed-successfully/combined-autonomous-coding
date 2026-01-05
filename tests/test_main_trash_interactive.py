import unittest
from unittest.mock import patch, MagicMock
import sys
import io
from pathlib import Path
import tempfile
import shutil
import argparse

# Ensure the module can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run_trash

class TestTrashInteractiveRestore(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.trash_dir = self.project_dir / ".agent_trash"
        self.trash_dir.mkdir()

        # Create some dummy archives
        self.archive1_dir = self.trash_dir / "trash-2023-01-01_10-00-00"
        self.archive1_dir.mkdir()
        (self.archive1_dir / "file1.txt").write_text("file1 content")

        self.archive2_dir = self.trash_dir / "trash-2023-01-02_12-00-00"
        self.archive2_dir.mkdir()
        (self.archive2_dir / "file2.txt").write_text("file2 content")

        self.archive3_dir = self.trash_dir / "trash-2023-01-03_14-00-00"
        self.archive3_dir.mkdir()
        (self.archive3_dir / "file3.txt").write_text("file3 content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('builtins.input', side_effect=['2'])  # Simulate user selecting the second archive
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_interactive_restore_selects_correct_archive(self, mock_stdout, mock_input):
        args = argparse.Namespace(
            action="restore",
            archive_name=None,
            file_name=None,
            project_dir=self.project_dir,
            all=False,
            yes=True,  # Bypasses the confirmation prompt
            dry_run=False
        )

        with self.assertRaises(SystemExit) as cm:
            run_trash(args)

        self.assertEqual(cm.exception.code, 0)

        # The archives are sorted in reverse chronological order (newest first)
        # So, the list presented to the user would be:
        # 1. trash-2023-01-03_14-00-00
        # 2. trash-2023-01-02_12-00-00
        # 3. trash-2023-01-01_10-00-00
        #
        # User input '2' selects 'trash-2023-01-02_12-00-00'

        # Check that the correct file was restored
        restored_file = self.project_dir / "file2.txt"
        self.assertTrue(restored_file.exists())
        self.assertEqual(restored_file.read_text(), "file2 content")

        # Check that the other files were NOT restored
        self.assertFalse((self.project_dir / "file1.txt").exists())
        self.assertFalse((self.project_dir / "file3.txt").exists())

        # Check that the restored archive was removed from the trash
        self.assertFalse(self.archive2_dir.exists())

        # Check that the other archives remain in the trash
        self.assertTrue(self.archive1_dir.exists())
        self.assertTrue(self.archive3_dir.exists())

        # Verify the output
        output = mock_stdout.getvalue()
        self.assertIn("Please select an archive to restore:", output)
        self.assertIn("[1] trash-2023-01-03_14-00-00", output)
        self.assertIn("[2] trash-2023-01-02_12-00-00", output)
        self.assertIn("[3] trash-2023-01-01_10-00-00", output)
        self.assertIn("Restored: file2.txt", output)
        self.assertIn("✅ Restore complete.", output)

if __name__ == '__main__':
    unittest.main()
