import unittest
import shutil
import tempfile
import stat
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.hooks import install_pre_commit_hook, uninstall_pre_commit_hook, run_hooks_logic

class TestHooks(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.git_dir = self.test_dir / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        self.git_dir.mkdir()
        self.hooks_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_install_pre_commit_hook(self):
        # Test basic installation
        result = install_pre_commit_hook(self.test_dir, python_exe="python3", agent_script="/path/to/main.py")
        self.assertTrue(result)

        hook_path = self.hooks_dir / "pre-commit"
        self.assertTrue(hook_path.exists())
        self.assertTrue(bool(os.stat(hook_path).st_mode & stat.S_IEXEC))

        content = hook_path.read_text()
        self.assertIn("Combined Autonomous Coding Agent", content)
        self.assertIn('PYTHON_EXE="python3"', content)
        self.assertIn('AGENT_SCRIPT="/path/to/main.py"', content)

    def test_install_pre_commit_hook_not_git(self):
        # Test install on non-git dir
        non_git_dir = self.test_dir / "nongit"
        non_git_dir.mkdir()

        # Suppress print
        with patch('builtins.print'):
            result = install_pre_commit_hook(non_git_dir)
        self.assertFalse(result)

    def test_install_pre_commit_hook_existing_overwrite_protection(self):
        # Create an existing hook not managed by us
        hook_path = self.hooks_dir / "pre-commit"
        hook_path.write_text("#!/bin/sh\necho 'existing'")

        with patch('builtins.print'):
            result = install_pre_commit_hook(self.test_dir)
        self.assertFalse(result)
        self.assertEqual(hook_path.read_text(), "#!/bin/sh\necho 'existing'")

    def test_install_pre_commit_hook_reinstall(self):
        # First install
        install_pre_commit_hook(self.test_dir, python_exe="python3", agent_script="/path/to/main.py")

        # Second install (should pass because it detects it is ours)
        result = install_pre_commit_hook(self.test_dir, python_exe="python3", agent_script="/path/to/main.py")
        self.assertTrue(result)

    def test_uninstall_pre_commit_hook(self):
        # Install then uninstall
        install_pre_commit_hook(self.test_dir, python_exe="python3", agent_script="/path/to/main.py")

        result = uninstall_pre_commit_hook(self.test_dir)
        self.assertTrue(result)
        self.assertFalse((self.hooks_dir / "pre-commit").exists())

    def test_uninstall_pre_commit_hook_foreign(self):
        # Create foreign hook
        hook_path = self.hooks_dir / "pre-commit"
        hook_path.write_text("#!/bin/sh\necho 'foreign'")

        with patch('builtins.print'):
            result = uninstall_pre_commit_hook(self.test_dir)
        self.assertTrue(result)
        self.assertTrue(hook_path.exists())

    def test_uninstall_pre_commit_hook_no_hook(self):
        result = uninstall_pre_commit_hook(self.test_dir)
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_run_hooks_logic_success(self, mock_run):
        mock_run.return_value.returncode = 0

        with patch('builtins.print'):
            result = run_hooks_logic(self.test_dir)

        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2) # lint and test

        # Verify calls
        args_list = mock_run.call_args_list
        self.assertIn("lint", args_list[0][0][0])
        self.assertIn("test", args_list[1][0][0])

    @patch('subprocess.run')
    def test_run_hooks_logic_failure(self, mock_run):
        # Fail on first call (lint)
        mock_run.return_value.returncode = 1

        with patch('builtins.print'):
            result = run_hooks_logic(self.test_dir)

        self.assertFalse(result)
        self.assertEqual(mock_run.call_count, 1)
