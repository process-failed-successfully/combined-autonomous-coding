import unittest
import os
import shutil
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the code to test
# We need to add the repository root to sys.path to import modules
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.hooks import install_hooks, run_hooks_logic, uninstall_hooks

class TestHooksConfigurable(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        self.git_dir = self.project_dir / ".git"
        self.hooks_dir = self.git_dir / "hooks"
        self.config_path = self.project_dir / "agent_config.yaml"

        # Simulate git repo
        self.git_dir.mkdir()
        self.hooks_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_install_defaults(self):
        """Test installing default hooks when no config is present."""
        # No agent_config.yaml created
        success = install_hooks(self.project_dir)
        self.assertTrue(success)

        pre_commit_hook = self.hooks_dir / "pre-commit"
        self.assertTrue(pre_commit_hook.exists())
        self.assertTrue(os.access(pre_commit_hook, os.X_OK))

        content = pre_commit_hook.read_text()
        self.assertIn("hooks run pre-commit", content)

    def test_install_configurable(self):
        """Test installing hooks defined in configuration."""
        config_data = {
            "git_hooks": {
                "pre-push": ["echo 'pushing'"],
                "commit-msg": [{"command": "check-msg", "args": ["--strict"]}]
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(config_data, f)

        success = install_hooks(self.project_dir)
        self.assertTrue(success)

        # pre-commit should NOT exist because it wasn't in config
        self.assertFalse((self.hooks_dir / "pre-commit").exists())

        # pre-push and commit-msg should exist
        self.assertTrue((self.hooks_dir / "pre-push").exists())
        self.assertTrue((self.hooks_dir / "commit-msg").exists())

        # Check content
        content = (self.hooks_dir / "pre-push").read_text()
        self.assertIn("hooks run pre-push", content)

    @patch("subprocess.run")
    def test_run_logic_default(self, mock_run):
        """Test running hooks with default logic (no hook name)."""
        mock_run.return_value.returncode = 0

        # Should run lint and test
        success = run_hooks_logic(self.project_dir, hook_name=None)
        self.assertTrue(success)

        # Verify calls
        # We expect 2 calls: lint and test
        self.assertEqual(mock_run.call_count, 2)

        # Check command structure. args[0] is the command string/list
        # run_hooks_logic uses subprocess.run with list args for default logic in my implementation?
        # Actually in the new implementation:
        # commands = [
        #    {"command": "lint", "args": ["--project-dir", str(project_dir)]},
        #    {"command": "test", "args": ["--project-dir", str(project_dir)]}
        # ]
        # And execution logic:
        # args = [python_exe, agent_script, sub_cmd] + sub_args

        # Let's inspect the calls
        args, _ = mock_run.call_args_list[0]
        cmd_list = args[0]
        self.assertIn("lint", cmd_list)
        self.assertIn("--project-dir", cmd_list)

        args, _ = mock_run.call_args_list[1]
        cmd_list = args[0]
        self.assertIn("test", cmd_list)

    @patch("subprocess.run")
    def test_run_logic_named(self, mock_run):
        """Test running a specific named hook from config."""
        config_data = {
            "git_hooks": {
                "pre-push": [
                    "echo 'raw shell command'",
                    {"command": "security", "args": ["--scan-type", "quick"]}
                ]
            }
        }
        with open(self.config_path, "w") as f:
            yaml.dump(config_data, f)

        mock_run.return_value.returncode = 0

        success = run_hooks_logic(self.project_dir, hook_name="pre-push")
        self.assertTrue(success)

        self.assertEqual(mock_run.call_count, 2)

        # Call 1: Shell command
        args1, kwargs1 = mock_run.call_args_list[0]
        self.assertEqual(args1[0], "echo 'raw shell command'")
        self.assertTrue(kwargs1.get("shell"))

        # Call 2: Internal command
        args2, kwargs2 = mock_run.call_args_list[1]
        cmd_list = args2[0]
        self.assertIn("security", cmd_list)
        self.assertIn("--scan-type", cmd_list)
        # It should auto-inject --project-dir
        self.assertIn("--project-dir", cmd_list)

    @patch("subprocess.run")
    def test_run_logic_missing_config(self, mock_run):
        """Test running a hook that isn't in config."""
        success = run_hooks_logic(self.project_dir, hook_name="non-existent")
        self.assertFalse(success)
        mock_run.assert_not_called()

    def test_uninstall(self):
        """Test uninstalling hooks."""
        install_hooks(self.project_dir)
        self.assertTrue((self.hooks_dir / "pre-commit").exists())

        success = uninstall_hooks(self.project_dir)
        self.assertTrue(success)
        self.assertFalse((self.hooks_dir / "pre-commit").exists())

if __name__ == "__main__":
    unittest.main()
