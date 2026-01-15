import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
import os
import sys
from pathlib import Path
import tempfile
import shutil

from shared.watch_handler import CommandEventHandler, _determine_default_command

class TestWatchCommand(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_determine_default_command_python_pytest(self):
        (self.project_dir / "pyproject.toml").touch()
        with patch('shutil.which', return_value='/usr/bin/pytest'):
            command = _determine_default_command(self.project_dir)
            self.assertEqual(command, ["pytest"])

    def test_determine_default_command_python_unittest(self):
        (self.project_dir / "requirements.txt").touch()
        with patch('shutil.which', return_value=None):
            command = _determine_default_command(self.project_dir)
            self.assertEqual(command, [sys.executable, "-m", "unittest", "discover"])

    def test_determine_default_command_npm(self):
        (self.project_dir / "package.json").touch()
        command = _determine_default_command(self.project_dir)
        self.assertEqual(command, ["npm", "test"])

    def test_determine_default_command_pnpm(self):
        (self.project_dir / "package.json").touch()
        (self.project_dir / "pnpm-lock.yaml").touch()
        command = _determine_default_command(self.project_dir)
        self.assertEqual(command, ["pnpm", "test"])

    def test_determine_default_command_yarn(self):
        (self.project_dir / "package.json").touch()
        (self.project_dir / "yarn.lock").touch()
        command = _determine_default_command(self.project_dir)
        self.assertEqual(command, ["yarn", "test"])

    def test_determine_default_command_go(self):
        (self.project_dir / "go.mod").touch()
        command = _determine_default_command(self.project_dir)
        self.assertEqual(command, ["go", "test", "./..."])

    def test_determine_default_command_unknown(self):
        command = _determine_default_command(self.project_dir)
        self.assertIsNone(command)

    @patch('subprocess.run')
    def test_command_event_handler_custom_command(self, mock_subprocess_run):
        handler = CommandEventHandler(["my-custom-command"], self.project_dir)
        self.assertEqual(handler.command, ["my-custom-command"])

        # The initial run in the constructor
        mock_subprocess_run.assert_called_once_with(["my-custom-command"], cwd=self.project_dir)

        event = MagicMock()
        event.is_directory = False
        event.src_path = str(self.project_dir / "some_file.py")
        handler.on_any_event(event)

        self.assertEqual(mock_subprocess_run.call_count, 2)
        mock_subprocess_run.assert_called_with(["my-custom-command"], cwd=self.project_dir)

    @patch('subprocess.run')
    def test_command_event_handler_default_command(self, mock_subprocess_run):
        (self.project_dir / "pyproject.toml").touch()
        with patch('shutil.which', return_value='/usr/bin/pytest'):
            handler = CommandEventHandler(None, self.project_dir)
            self.assertEqual(handler.command, ["pytest"])

        # The initial run in the constructor
        mock_subprocess_run.assert_called_once_with(["pytest"], cwd=self.project_dir)

        event = MagicMock()
        event.is_directory = False
        event.src_path = str(self.project_dir / "some_file.py")
        handler.on_any_event(event)

        self.assertEqual(mock_subprocess_run.call_count, 2)
        mock_subprocess_run.assert_called_with(["pytest"], cwd=self.project_dir)

    @patch('subprocess.run')
    def test_command_event_handler_ignored_directory(self, mock_subprocess_run):
        git_dir = self.project_dir / ".git"
        git_dir.mkdir()
        handler = CommandEventHandler(["some-command"], self.project_dir)
        mock_subprocess_run.assert_called_once() # From constructor

        event = MagicMock()
        event.is_directory = False
        event.src_path = str(git_dir / "some_file")
        handler.on_any_event(event)

        # Should not have been called again
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    def test_command_event_handler_is_directory(self, mock_subprocess_run):
        handler = CommandEventHandler(["some-command"], self.project_dir)
        mock_subprocess_run.assert_called_once() # From constructor

        event = MagicMock()
        event.is_directory = True
        event.src_path = str(self.project_dir / "some_dir")
        handler.on_any_event(event)

        # Should not have been called again
        mock_subprocess_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
