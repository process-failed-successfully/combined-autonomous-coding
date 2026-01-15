import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import sys
import shutil

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shared.deps_manager import (
    detect_project_type,
    add_dependency,
    remove_dependency,
    list_dependencies,
    sync_dependencies,
)

import tempfile

class TestDepsManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        # Create dummy files for detection
        (self.test_dir / "requirements.txt").touch()
        (self.test_dir / "package.json").touch()
        (self.test_dir / "yarn.lock").touch()
        (self.test_dir / "pnpm-lock.yaml").touch()

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch('shutil.which')
    def test_detect_project_type(self, mock_which):
        mock_which.return_value = '/usr/bin/some_tool'
        # Test pnpm detection
        self.assertEqual(detect_project_type(self.test_dir), "pnpm")
        (self.test_dir / "pnpm-lock.yaml").unlink()
        # Test yarn detection
        self.assertEqual(detect_project_type(self.test_dir), "yarn")
        (self.test_dir / "yarn.lock").unlink()
        # Test npm detection
        self.assertEqual(detect_project_type(self.test_dir), "npm")
        (self.test_dir / "package.json").unlink()
        # Test pip detection
        self.assertEqual(detect_project_type(self.test_dir), "pip")
        (self.test_dir / "requirements.txt").unlink()
        # Test no project type
        self.assertIsNone(detect_project_type(self.test_dir))

    @patch('subprocess.run')
    @patch('shared.deps_manager.detect_project_type')
    def test_add_dependency(self, mock_detect, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        # Test pip
        mock_detect.return_value = "pip"
        req_file = self.test_dir / "requirements.txt"
        req_file.write_text("")  # Start with an empty file

        self.assertTrue(add_dependency(self.test_dir, "requests"))
        self.assertEqual("requests", req_file.read_text().strip())
        mock_run.assert_called_with([sys.executable, "-m", "pip", "install", "requests"], cwd=self.test_dir, capture_output=True, text=True)

        # Test adding to a non-empty file
        self.assertTrue(add_dependency(self.test_dir, "flask"))
        self.assertEqual("requests\nflask", req_file.read_text().strip())
        mock_run.assert_called_with([sys.executable, "-m", "pip", "install", "flask"], cwd=self.test_dir, capture_output=True, text=True)

        # Test npm
        mock_detect.return_value = "npm"
        self.assertTrue(add_dependency(self.test_dir, "react"))
        mock_run.assert_called_with(["npm", "install", "react", "--save"], cwd=self.test_dir, capture_output=True, text=True)

        # Test yarn
        mock_detect.return_value = "yarn"
        self.assertTrue(add_dependency(self.test_dir, "lodash"))
        mock_run.assert_called_with(["yarn", "add", "lodash"], cwd=self.test_dir, capture_output=True, text=True)

        # Test pnpm
        mock_detect.return_value = "pnpm"
        self.assertTrue(add_dependency(self.test_dir, "vite"))
        mock_run.assert_called_with(["pnpm", "add", "vite"], cwd=self.test_dir, capture_output=True, text=True)

    @patch('subprocess.run')
    @patch('shared.deps_manager.detect_project_type')
    def test_remove_dependency(self, mock_detect, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        # Test pip with various formats
        mock_detect.return_value = "pip"
        (self.test_dir / "requirements.txt").write_text(
            "requests==2.25.1\n"
            "flask>=1.1.2\n"
            "numpy\n"
            "pandas[extra]==1.2.3\n"
            "scipy"
        )
        remove_dependency(self.test_dir, "requests")
        remove_dependency(self.test_dir, "flask")
        remove_dependency(self.test_dir, "pandas")
        self.assertEqual(
            (self.test_dir / "requirements.txt").read_text(),
            "numpy\nscipy"
        )
        mock_run.assert_any_call([sys.executable, "-m", "pip", "uninstall", "-y", "requests"], cwd=self.test_dir, capture_output=True, text=True)
        mock_run.assert_any_call([sys.executable, "-m", "pip", "uninstall", "-y", "flask"], cwd=self.test_dir, capture_output=True, text=True)
        mock_run.assert_any_call([sys.executable, "-m", "pip", "uninstall", "-y", "pandas"], cwd=self.test_dir, capture_output=True, text=True)


        # Test npm
        mock_detect.return_value = "npm"
        remove_dependency(self.test_dir, "react")
        mock_run.assert_called_with(["npm", "uninstall", "react", "--save"], cwd=self.test_dir, capture_output=True, text=True)

    @patch('shared.deps_manager.detect_project_type')
    def test_list_dependencies(self, mock_detect):
        with patch('sys.stdout', new_callable=__import__('io').StringIO) as mock_stdout:
            # Test pip
            mock_detect.return_value = "pip"
            (self.test_dir / "requirements.txt").write_text("requests\nflask")
            list_dependencies(self.test_dir)
            self.assertIn("requests\nflask", mock_stdout.getvalue())

            # Test npm
            mock_stdout.seek(0)
            mock_stdout.truncate(0)
            mock_detect.return_value = "npm"
            (self.test_dir / "package.json").write_text('{"dependencies": {"react": "17.0.0"}}')
            list_dependencies(self.test_dir)
            self.assertIn("react@17.0.0", mock_stdout.getvalue())

    @patch('subprocess.run')
    @patch('shared.deps_manager.detect_project_type')
    def test_sync_dependencies(self, mock_detect, mock_run):
        mock_run.return_value = MagicMock(returncode=0)

        # Test pip
        mock_detect.return_value = "pip"
        sync_dependencies(self.test_dir)
        mock_run.assert_called_with([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=self.test_dir, capture_output=True, text=True)

        # Test npm
        mock_detect.return_value = "npm"
        sync_dependencies(self.test_dir)
        mock_run.assert_called_with(["npm", "install"], cwd=self.test_dir, capture_output=True, text=True)

if __name__ == '__main__':
    unittest.main()
