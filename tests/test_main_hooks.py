import unittest
import shutil
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch
from main import run_hooks
import argparse

class TestMainHooks(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.git_dir = self.test_dir / ".git"
        self.git_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shared.hooks.install_hooks')
    def test_run_hooks_install(self, mock_install):
        args = argparse.Namespace(
            action="install",
            project_dir=self.test_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_hooks(args)

        self.assertEqual(cm.exception.code, 0)
        mock_install.assert_called_once_with(self.test_dir)

    @patch('shared.hooks.uninstall_hooks')
    def test_run_hooks_uninstall(self, mock_uninstall):
        args = argparse.Namespace(
            action="uninstall",
            project_dir=self.test_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_hooks(args)

        self.assertEqual(cm.exception.code, 0)
        mock_uninstall.assert_called_once_with(self.test_dir)

    @patch('shared.hooks.run_hooks_logic')
    def test_run_hooks_run_success(self, mock_run):
        mock_run.return_value = True
        args = argparse.Namespace(
            action="run",
            project_dir=self.test_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_hooks(args)

        self.assertEqual(cm.exception.code, 0)
        mock_run.assert_called_once_with(self.test_dir, hook_name=None)

    @patch('shared.hooks.run_hooks_logic')
    def test_run_hooks_run_failure(self, mock_run):
        mock_run.return_value = False
        args = argparse.Namespace(
            action="run",
            project_dir=self.test_dir
        )
        with self.assertRaises(SystemExit) as cm:
            run_hooks(args)

        self.assertEqual(cm.exception.code, 1)
        mock_run.assert_called_once_with(self.test_dir, hook_name=None)
