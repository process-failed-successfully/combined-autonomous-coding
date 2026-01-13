import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import tarfile
import tempfile
import shutil
import os

from main import run_share, run_import


class TestShareImport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

        # Create some dummy files
        (self.project_dir / "main.py").write_text("print('hello')")
        (self.project_dir / "README.md").write_text("# Test Project")
        (self.project_dir / ".agent_history").write_text("run1\nrun2")
        (self.project_dir / "feature_list.json").write_text('{"features": []}')

        # Create dummy log files in the central location
        self.repo_root = Path(__file__).parent.parent
        self.logs_dir = self.repo_root / "agents/logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / "run1.log").write_text("Log for run 1")
        (self.logs_dir / "run2.log").write_text("Log for run 2")

        # Mock subprocess for git
        self.mock_subprocess_run = patch('subprocess.run').start()
        self.mock_subprocess_run.return_value = MagicMock(
            stdout=b'', stderr=b'', returncode=0
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        patch.stopall()
        # Clean up dummy log files
        if (self.logs_dir / "run1.log").exists():
            (self.logs_dir / "run1.log").unlink()
        if (self.logs_dir / "run2.log").exists():
            (self.logs_dir / "run2.log").unlink()

    def test_share_command_creates_archive(self):
        output_file = Path(self.test_dir) / "shared_project.tar.gz"
        args = MagicMock(project_dir=self.project_dir, output_file=output_file)

        with self.assertRaises(SystemExit) as cm:
            run_share(args)
        self.assertEqual(cm.exception.code, 0)

        self.assertTrue(output_file.exists())

        # Verify the contents of the archive
        with tarfile.open(output_file, "r:gz") as tar:
            names = tar.getnames()
            self.assertIn("test_project/main.py", names)
            self.assertIn("test_project/README.md", names)
            self.assertIn("test_project/.agent_history", names)
            self.assertIn("test_project/feature_list.json", names)
            self.assertIn("test_project/.agent_logs/run1.log", names)
            self.assertIn("test_project/.agent_logs/run2.log", names)

    def test_import_command_extracts_archive(self):
        # First, create an archive to import
        archive_file = Path(self.test_dir) / "project_to_import.tar.gz"
        share_args = MagicMock(project_dir=self.project_dir, output_file=archive_file)
        with self.assertRaises(SystemExit) as cm:
            run_share(share_args)
        self.assertEqual(cm.exception.code, 0)

        # Now, import it to a new directory
        import_dir = Path(self.test_dir) / "imported_project_dir"
        import_dir.mkdir()
        import_args = MagicMock(archive_file=archive_file, output_dir=import_dir)

        with self.assertRaises(SystemExit) as cm:
            run_import(import_args)
        self.assertEqual(cm.exception.code, 0)

        # Verify the extracted files
        extracted_project_dir = import_dir / "test_project"
        self.assertTrue(extracted_project_dir.exists())
        self.assertTrue((extracted_project_dir / "main.py").exists())
        self.assertTrue((extracted_project_dir / "README.md").exists())
        self.assertTrue((extracted_project_dir / ".agent_history").exists())
        self.assertTrue((extracted_project_dir / "feature_list.json").exists())

        # Verify that logs were restored to the central location
        self.assertTrue((self.logs_dir / "run1.log").exists())
        self.assertTrue((self.logs_dir / "run2.log").exists())
        # The staged logs directory should be removed after import
        self.assertFalse((extracted_project_dir / ".agent_logs").exists())


if __name__ == '__main__':
    unittest.main()
