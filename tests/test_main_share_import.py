
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path
import tarfile
import tempfile
import shutil
import subprocess

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_share, run_import

class TestShareImport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "project"
        self.project_dir.mkdir()

        # Initialize a git repository to test .gitignore functionality
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=self.project_dir, capture_output=True)

        (self.project_dir / "file1.txt").write_text("content1")
        (self.project_dir / "file2.txt").write_text("content2")
        (self.project_dir / ".gitignore").write_text("ignored.txt\n")
        (self.project_dir / "ignored.txt").write_text("ignored_content")
        (self.project_dir / ".agent_history").write_text("run123\n")

        # Mock the log file
        self.repo_root = Path(__file__).parent.parent
        self.logs_dir = self.repo_root / "agents/logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "run123.log").write_text("log content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        log_file = self.logs_dir / "run123.log"
        if log_file.exists():
            log_file.unlink()
        if self.logs_dir.exists() and not os.listdir(self.logs_dir):
            self.logs_dir.rmdir()

    def test_share_command(self):
        # Create a mock for args
        args = MagicMock()
        args.project_dir = self.project_dir
        args.output = self.project_dir / "test_archive.tar.gz"

        with patch('sys.exit') as mock_exit:
            run_share(args)
            mock_exit.assert_called_once_with(0)

        # Verify the archive
        self.assertTrue(args.output.exists())
        with tarfile.open(args.output, "r:gz") as tar:
            names = tar.getnames()
            self.assertIn("file1.txt", names)
            self.assertIn("file2.txt", names)
            self.assertIn(".agent_history", names)
            self.assertIn(".agent_logs/run123.log", names)
            self.assertNotIn("ignored.txt", names)

    def test_import_command_clean(self):
        # First, create an archive to import
        archive_path = self.project_dir / "test_archive.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.project_dir / "file1.txt", arcname="file1.txt")
            tar.add(self.project_dir / "file2.txt", arcname="file2.txt")

        # Create a new directory to import into
        import_dir = Path(self.test_dir) / "import_project"
        import_dir.mkdir()

        args = MagicMock()
        args.project_dir = import_dir
        args.archive_path = archive_path
        args.force = False

        with patch('sys.exit') as mock_exit:
            run_import(args)
            mock_exit.assert_called_once_with(0)

        self.assertTrue((import_dir / "file1.txt").exists())
        self.assertTrue((import_dir / "file2.txt").exists())
        self.assertEqual((import_dir / "file1.txt").read_text(), "content1")

    def test_import_command_with_conflict_no_force(self):
        # Create an archive
        archive_path = self.project_dir / "test_archive.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.project_dir / "file1.txt", arcname="file1.txt")

        # Create a conflicting file in the import directory
        import_dir = Path(self.test_dir) / "import_project"
        import_dir.mkdir()
        (import_dir / "file1.txt").write_text("conflicting_content")

        args = MagicMock()
        args.project_dir = import_dir
        args.archive_path = archive_path
        args.force = False

        with patch('sys.exit') as mock_exit:
            run_import(args)
            mock_exit.assert_called_once_with(1)

        # Check that the file was not overwritten
        self.assertEqual((import_dir / "file1.txt").read_text(), "conflicting_content")

    def test_import_command_with_conflict_with_force(self):
        # Create an archive
        archive_path = self.project_dir / "test_archive.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.project_dir / "file1.txt", arcname="file1.txt")

        # Create a conflicting file in the import directory
        import_dir = Path(self.test_dir) / "import_project"
        import_dir.mkdir()
        (import_dir / "file1.txt").write_text("conflicting_content")

        args = MagicMock()
        args.project_dir = import_dir
        args.archive_path = archive_path
        args.force = True

        with patch('sys.exit') as mock_exit:
            run_import(args)
            mock_exit.assert_called_once_with(0)

        # Check that the file was overwritten
        self.assertEqual((import_dir / "file1.txt").read_text(), "content1")

    def test_import_command_traversal_attack(self):
        # Create a malicious archive
        archive_path = self.project_dir / "malicious.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            # Create a file with a traversal path
            info = tarfile.TarInfo(name="../pwned.txt")
            tar.addfile(info)

        import_dir = Path(self.test_dir) / "import_project"
        import_dir.mkdir()

        args = MagicMock()
        args.project_dir = import_dir
        args.archive_path = archive_path
        args.force = False

        with patch('sys.exit') as mock_exit:
            run_import(args)
            mock_exit.assert_called_once_with(1)

        # Ensure the malicious file was not created
        self.assertFalse((Path(self.test_dir) / "pwned.txt").exists())

if __name__ == '__main__':
    unittest.main()
