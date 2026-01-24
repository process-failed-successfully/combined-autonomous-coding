import unittest
import shutil
import tempfile
import sys
import stat
from pathlib import Path
from unittest.mock import patch
from shared.hooks import install_hooks, uninstall_hooks, run_hook_logic

class TestHooksConfigurable(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.git_dir = self.test_dir / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        # Ensure parent dirs exist
        self.git_dir.mkdir(parents=True, exist_ok=True)
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_install_hooks_custom_config(self):
        config = {
            "pre-commit": ["lint", "test"],
            "pre-push": ["security"]
        }

        result = install_hooks(self.test_dir, config, python_exe="python3", agent_script="/app/main.py")
        self.assertTrue(result)

        # Check pre-commit
        pre_commit_path = self.hooks_dir / "pre-commit"
        self.assertTrue(pre_commit_path.exists())
        self.assertTrue(bool(pre_commit_path.stat().st_mode & stat.S_IEXEC))
        content = pre_commit_path.read_text()
        self.assertIn('hooks run "pre-commit"', content)

        # Check pre-push
        pre_push_path = self.hooks_dir / "pre-push"
        self.assertTrue(pre_push_path.exists())
        self.assertTrue(bool(pre_push_path.stat().st_mode & stat.S_IEXEC))
        content = pre_push_path.read_text()
        self.assertIn('hooks run "pre-push"', content)

    def test_install_hooks_empty_config(self):
        result = install_hooks(self.test_dir, {}, python_exe="python3", agent_script="/app/main.py")
        self.assertTrue(result)
        # Should not create any hooks (ignore if dir exists and is empty or contains sample)
        # We start with empty hooks dir so it should be empty
        self.assertEqual(len(list(self.hooks_dir.iterdir())), 0)

    def test_uninstall_hooks_removes_all(self):
        # Create dummy hooks
        (self.hooks_dir / "pre-commit").write_text("Combined Autonomous Coding Agent")
        (self.hooks_dir / "pre-push").write_text("Combined Autonomous Coding Agent")
        (self.hooks_dir / "commit-msg").write_text("Something else") # Should not be removed

        result = uninstall_hooks(self.test_dir)
        self.assertTrue(result)

        self.assertFalse((self.hooks_dir / "pre-commit").exists())
        self.assertFalse((self.hooks_dir / "pre-push").exists())
        self.assertTrue((self.hooks_dir / "commit-msg").exists())

    @patch('subprocess.run')
    def test_run_hook_logic_executes_commands(self, mock_run):
        mock_run.return_value.returncode = 0

        config = {
            "pre-commit": ["lint", "test --unit"],
            "custom-hook": ["echo hello"]
        }

        # Run pre-commit
        with patch('builtins.print'):
            result = run_hook_logic(self.test_dir, "pre-commit", config)
        self.assertTrue(result)

        # Should run twice
        self.assertEqual(mock_run.call_count, 2)

        # Verify calls
        # Call 1: lint
        args1 = mock_run.call_args_list[0][0][0]
        # Since we use sys.executable and agent script, the first arg is python
        self.assertIn("lint", args1)
        self.assertIn("--project-dir", args1)

        # Call 2: test
        args2 = mock_run.call_args_list[1][0][0]
        self.assertIn("test", args2)
        self.assertIn("--unit", args2)

    @patch('subprocess.run')
    def test_run_hook_logic_shell_command(self, mock_run):
        mock_run.return_value.returncode = 0

        config = {
            "deploy": ["./deploy.sh prod"]
        }

        with patch('builtins.print'):
            result = run_hook_logic(self.test_dir, "deploy", config)
        self.assertTrue(result)

        args = mock_run.call_args_list[0][0][0]
        self.assertEqual(args[0], "./deploy.sh")
        self.assertEqual(args[1], "prod")

    @patch('subprocess.run')
    def test_run_hook_logic_failure(self, mock_run):
        mock_run.return_value.returncode = 1

        config = {"pre-commit": ["lint", "test"]}

        with patch('builtins.print'):
            result = run_hook_logic(self.test_dir, "pre-commit", config)
        self.assertFalse(result)
        # Should stop after first failure
        self.assertEqual(mock_run.call_count, 1)

if __name__ == "__main__":
    unittest.main()
