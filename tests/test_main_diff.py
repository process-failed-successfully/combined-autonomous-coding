import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import argparse
import sys

# Ensure the main script can be imported
from main import run_diff, _find_commit_by_run_id

class TestDiffCommand(unittest.TestCase):

    def setUp(self):
        # Create a mock for subprocess.run
        self.mock_subprocess_run = patch('subprocess.run').start()
        self.mock_subprocess_run.return_value = MagicMock(returncode=0)

        # Create a mock for shutil.which
        self.mock_shutil_which = patch('shutil.which').start()
        self.mock_shutil_which.return_value = '/usr/bin/git'

        # Create a mock for _find_commit_by_run_id
        self.mock_find_commit = patch('main._find_commit_by_run_id').start()
        self.mock_find_commit.side_effect = self._mock_resolver

        # Mock Path.exists and is_dir
        self.mock_path_exists = patch('pathlib.Path.exists').start()
        self.mock_path_exists.return_value = True
        self.mock_path_is_dir = patch('pathlib.Path.is_dir').start()
        self.mock_path_is_dir.return_value = True

    def tearDown(self):
        patch.stopall()

    def _mock_resolver(self, project_dir, git_path, run_id):
        if run_id == "run-123":
            return "abc1234"
        if run_id == "run-456":
            return "def5678"
        return None

    def test_diff_no_args(self):
        """Test `diff` with no arguments (shows uncommitted changes)."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1=None,
            ref2=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(Path('.').resolve()), 'diff', '--color=always', 'HEAD']
        )

    def test_diff_one_git_ref(self):
        """Test `diff <ref1>` with a git reference."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1='main',
            ref2=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(Path('.').resolve()), 'diff', '--color=always', 'main']
        )

    def test_diff_one_run_id(self):
        """Test `diff <ref1>` with a Run ID."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1='run-123',
            ref2=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        resolved_path = Path('.').resolve()
        self.mock_find_commit.assert_called_once_with(resolved_path, '/usr/bin/git', 'run-123')
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(resolved_path), 'diff', '--color=always', 'abc1234']
        )

    def test_diff_two_git_refs(self):
        """Test `diff <ref1> <ref2>` with two git references."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1='main',
            ref2='develop'
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(Path('.').resolve()), 'diff', '--color=always', 'main', 'develop']
        )

    def test_diff_two_run_ids(self):
        """Test `diff <ref1> <ref2>` with two Run IDs."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1='run-123',
            ref2='run-456'
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(self.mock_find_commit.call_count, 2)
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(Path('.').resolve()), 'diff', '--color=always', 'abc1234', 'def5678']
        )

    def test_diff_mixed_ref_and_run_id(self):
        """Test `diff <ref1> <ref2>` with a git ref and a Run ID."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1='main',
            ref2='run-456'
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(self.mock_find_commit.call_count, 2)
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(Path('.').resolve()), 'diff', '--color=always', 'main', 'def5678']
        )

    def test_diff_invalid_run_id(self):
        """Test `diff` with a Run ID that does not resolve."""
        args = argparse.Namespace(
            project_dir=Path('.'),
            ref1='invalid-run-id',
            ref2=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 0)
        # It should fall back to using the raw ref
        self.mock_subprocess_run.assert_called_once_with(
            ['/usr/bin/git', '-C', str(Path('.').resolve()), 'diff', '--color=always', 'invalid-run-id']
        )

    def test_git_not_found(self):
        """Test that the command exits if git is not found."""
        self.mock_shutil_which.return_value = None
        args = argparse.Namespace(project_dir=Path('.'), ref1=None, ref2=None)
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 1)
        self.mock_subprocess_run.assert_not_called()

    def test_not_a_git_repo(self):
        """Test that the command exits if not in a git repository."""
        self.mock_path_exists.return_value = False
        args = argparse.Namespace(project_dir=Path('.'), ref1=None, ref2=None)
        with self.assertRaises(SystemExit) as cm:
            run_diff(args)
        self.assertEqual(cm.exception.code, 1)
        self.mock_subprocess_run.assert_not_called()

if __name__ == '__main__':
    unittest.main()
