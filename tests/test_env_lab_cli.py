import unittest
import argparse
from unittest.mock import patch, MagicMock
from pathlib import Path

# Assume run_env is in main
from main import run_env

class TestEnvLabCLI(unittest.TestCase):
    @patch('shared.tui.AgentTUI')
    @patch('main.asyncio.run')
    def test_run_env_tui(self, mock_asyncio_run, MockAgentTUI):
        """Test that `main.py env tui` correctly launches the AgentTUI with start_tab='tab-env'"""
        args = argparse.Namespace(
            action="tui",
            project_dir=Path("/tmp/fake_project")
        )

        # We need to catch sys.exit since run_env calls sys.exit(0)
        with self.assertRaises(SystemExit) as cm:
            run_env(args)

        self.assertEqual(cm.exception.code, 0)

        # Verify AgentTUI was initialized with correct arguments
        MockAgentTUI.assert_called_once_with(
            project_dir=Path("/tmp/fake_project").resolve(),
            start_tab="tab-env"
        )

        # Verify that asyncio.run was called on the run_async method
        mock_instance = MockAgentTUI.return_value
        mock_asyncio_run.assert_called_once_with(mock_instance.run_async())

if __name__ == "__main__":
    unittest.main()
