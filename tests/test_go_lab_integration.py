import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import argparse

# Ensure we can import from shared and main
sys.path.append(str(Path(__file__).parent.parent))

from shared.go_lab import run_go_lab_logic

class TestGoLabIntegration(unittest.TestCase):

    def setUp(self):
        # Create a mock args object similar to what argparse produces
        self.args = argparse.Namespace()
        self.args.project_dir = Path(".")
        self.args.package = None
        self.args.module_name = None

    @patch('shared.go_lab.GoLabManager.get_latest_version')
    def test_cli_info_command(self, mock_get_latest):
        self.args.action = "info"
        self.args.package = "example.com/foo"

        mock_get_latest.return_value = {"Version": "v1.0.0", "Time": "2023-01-01"}

        # Capture stdout to verify output
        with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
            success = run_go_lab_logic(self.args)

        self.assertTrue(success)
        mock_get_latest.assert_called_with("example.com/foo")

    @patch('shared.go_lab.GoLabManager.init_mod')
    def test_cli_init_command(self, mock_init):
        self.args.action = "init"
        self.args.module_name = "example.com/my-module"

        mock_init.return_value = True

        success = run_go_lab_logic(self.args)

        self.assertTrue(success)
        mock_init.assert_called_with("example.com/my-module")

    def test_cli_missing_package_arg(self):
        self.args.action = "info"
        self.args.package = None # simulating missing arg

        # Capture stderr to suppress error message during test
        with patch('sys.stderr', new_callable=MagicMock):
            success = run_go_lab_logic(self.args)

        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
