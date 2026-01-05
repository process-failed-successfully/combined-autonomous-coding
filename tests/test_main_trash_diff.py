import unittest
from unittest.mock import patch
import sys
import io
from pathlib import Path
import shutil
import tempfile
import asyncio
import main

class TestTrashDiff(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "project"
        self.project_dir.mkdir()
        self.trash_dir = self.project_dir / ".agent_trash"
        self.trash_dir.mkdir()

        self.archive_name = "trash-2023-01-01_12-00-00"
        self.archive_path = self.trash_dir / self.archive_name
        self.archive_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_trash_diff(self, args):
        full_args = ["main.py", "trash", "diff"] + args
        with patch.object(sys, "argv", full_args), \
             patch('sys.stdout', new_callable=io.StringIO) as mock_stdout, \
             self.assertRaises(SystemExit) as cm:
            asyncio.run(main.main())
        return cm.exception.code, mock_stdout.getvalue()

    def test_diff_modified_file(self):
        file_name = "test.txt"
        (self.project_dir / file_name).write_text("hello world\n")
        (self.archive_path / file_name).write_text("hello universe\n")

        exit_code, output = self._run_trash_diff([self.archive_name, file_name, "-p", str(self.project_dir)])

        self.assertEqual(exit_code, 0)
        self.assertIn(f"--- Diff for {file_name} ---", output)
        self.assertIn("-hello world", output)
        self.assertIn("+hello universe", output)

    def test_diff_deleted_file(self):
        file_name = "deleted.txt"
        (self.archive_path / file_name).write_text("I exist only in trash.\n")

        exit_code, output = self._run_trash_diff([self.archive_name, file_name, "-p", str(self.project_dir)])

        self.assertEqual(exit_code, 0)
        self.assertIn(f"--- a/{file_name} (Project Version)", output)
        self.assertIn(f"+++ b/{file_name} (Trashed Version in {self.archive_name})", output)
        self.assertIn(f"+I exist only in trash.", output)

    def test_diff_no_difference(self):
        file_name = "same.txt"
        content = "these files are the same.\n"
        (self.project_dir / file_name).write_text(content)
        (self.archive_path / file_name).write_text(content)

        exit_code, output = self._run_trash_diff([self.archive_name, file_name, "-p", str(self.project_dir)])

        self.assertEqual(exit_code, 0)
        self.assertIn(f"✅ No differences found between the trashed version and the project version of '{file_name}'.", output)

    def test_diff_archive_not_found(self):
        args = ['main.py', 'trash', 'diff', 'non_existent_archive', 'test.txt', '-p', str(self.project_dir)]
        with patch.object(sys, 'argv', args), \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr, \
             self.assertRaises(SystemExit) as cm:
            asyncio.run(main.main())

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Archive 'non_existent_archive' not found in trash.", mock_stderr.getvalue())

    def test_diff_file_not_in_archive(self):
        args = ['main.py', 'trash', 'diff', self.archive_name, 'not_a_file.txt', '-p', str(self.project_dir)]
        with patch.object(sys, 'argv', args), \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr, \
             self.assertRaises(SystemExit) as cm:
            asyncio.run(main.main())

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: File 'not_a_file.txt' not found in archive", mock_stderr.getvalue())

if __name__ == "__main__":
    unittest.main()
