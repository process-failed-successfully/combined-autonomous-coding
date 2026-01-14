import unittest
from unittest.mock import patch, MagicMock
import argparse
from pathlib import Path
import sys
from io import StringIO

from main import run_patch

class TestPatchCommand(unittest.TestCase):
    @patch('main.subprocess.run', autospec=True)
    @patch('main.shutil.which', autospec=True)
    @patch('pathlib.Path.read_text', autospec=True)
    @patch('pathlib.Path.is_file', autospec=True)
    @patch('pathlib.Path.is_dir', autospec=True)
    @patch('pathlib.Path.exists', autospec=True)
    def test_run_patch_from_file(self, mock_exists, mock_is_dir, mock_is_file, mock_read_text, mock_shutil_which, mock_subprocess_run):
        # Arrange
        mock_shutil_which.return_value = '/usr/bin/git'
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_is_file.return_value = True
        mock_read_text.return_value = 'test patch data'
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        project_dir = Path('.')
        args = argparse.Namespace(
            patch_file='test.patch',
            project_dir=project_dir,
            reverse=False
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(project_dir.resolve()), 'apply'],
            input='test patch data',
            text=True,
            capture_output=True
        )

    @patch('main.subprocess.run', autospec=True)
    @patch('main.shutil.which', autospec=True)
    @patch('pathlib.Path.is_dir', autospec=True)
    @patch('pathlib.Path.exists', autospec=True)
    def test_run_patch_from_stdin(self, mock_exists, mock_is_dir, mock_shutil_which, mock_subprocess_run):
        # Arrange
        mock_shutil_which.return_value = '/usr/bin/git'
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        project_dir = Path('.')
        args = argparse.Namespace(
            patch_file=None,
            project_dir=project_dir,
            reverse=False
        )

        with patch('sys.stdin', StringIO('stdin patch data')):
            # Act
            with self.assertRaises(SystemExit) as cm:
                run_patch(args)

            # Assert
            self.assertEqual(cm.exception.code, 0)
            mock_subprocess_run.assert_called_once_with(
                ['/usr/bin/git', '-C', str(project_dir.resolve()), 'apply'],
                input='stdin patch data',
                text=True,
                capture_output=True
            )

    @patch('main.subprocess.run', autospec=True)
    @patch('main.shutil.which', autospec=True)
    @patch('pathlib.Path.read_text', autospec=True)
    @patch('pathlib.Path.is_file', autospec=True)
    @patch('pathlib.Path.is_dir', autospec=True)
    @patch('pathlib.Path.exists', autospec=True)
    def test_run_patch_reverse(self, mock_exists, mock_is_dir, mock_is_file, mock_read_text, mock_shutil_which, mock_subprocess_run):
        # Arrange
        mock_shutil_which.return_value = '/usr/bin/git'
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_is_file.return_value = True
        mock_read_text.return_value = 'test patch data'
        mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        project_dir = Path('.')
        args = argparse.Namespace(
            patch_file='test.patch',
            project_dir=project_dir,
            reverse=True
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        # Assert
        self.assertEqual(cm.exception.code, 0)
        mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(project_dir.resolve()), 'apply', '--reverse'],
            input='test patch data',
            text=True,
            capture_output=True
        )

    @patch('main.shutil.which', autospec=True)
    @patch('pathlib.Path.is_file', autospec=True)
    @patch('pathlib.Path.is_dir', autospec=True)
    @patch('pathlib.Path.exists', autospec=True)
    def test_run_patch_file_not_found(self, mock_exists, mock_is_dir, mock_is_file, mock_shutil_which):
        # Arrange
        mock_shutil_which.return_value = '/usr/bin/git'
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_is_file.return_value = False

        args = argparse.Namespace(
            patch_file='non_existent.patch',
            project_dir=Path('.'),
            reverse=False
        )

        # Act
        with self.assertRaises(SystemExit) as cm:
            run_patch(args)

        # Assert
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()
