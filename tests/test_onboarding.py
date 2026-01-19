import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import io
import sys
from shared.onboarding import run_onboard_logic


class TestOnboarding(unittest.TestCase):
    @patch("shared.onboarding.get_suggestions")
    @patch("shared.onboarding._run_enhanced_status_logic")
    @patch("shared.onboarding.shutil.which")
    @patch("shared.onboarding.get_config_path")
    def test_run_onboard_logic_happy_path(self, mock_get_config, mock_which, mock_status, mock_suggestions):
        # Setup mocks
        mock_config_path = MagicMock(spec=Path)
        mock_config_path.exists.return_value = True
        mock_config_path.__str__.return_value = "/tmp/agent_config.yaml"
        mock_get_config.return_value = mock_config_path

        mock_which.return_value = "/usr/bin/git"
        mock_status.return_value = "Project Status: OK"
        mock_suggestions.return_value = [{"reason": "Do X", "command": "main.py x"}]

        project_dir = MagicMock(spec=Path)
        project_dir.resolve.return_value = project_dir
        project_dir.name = "TestProject"

        # Mock file existence checks for project type detection
        # Logic: (project_dir / "file").exists()
        # We need to ensure that when __truediv__ is called, the result has an .exists() method

        # Let's verify output contains what we expect

        captured_output = io.StringIO()
        sys.stdout = captured_output

        run_onboard_logic(project_dir)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("Welcome to Project: TestProject", output)
        self.assertIn("Configuration found", output)
        self.assertIn("Git installed", output)
        self.assertIn("Project Status: OK", output)
        self.assertIn("Recommended First Steps", output)
        self.assertIn("Do X", output)
        self.assertIn("Ready to Code", output)

    @patch("shared.onboarding.get_suggestions")
    @patch("shared.onboarding._run_enhanced_status_logic")
    @patch("shared.onboarding.shutil.which")
    @patch("shared.onboarding.get_config_path")
    def test_run_onboard_logic_missing_config(self, mock_get_config, mock_which, mock_status, mock_suggestions):
        mock_get_config.return_value = None
        mock_which.return_value = None  # No git
        mock_status.return_value = "Status"
        mock_suggestions.return_value = []

        project_dir = MagicMock(spec=Path)
        project_dir.resolve.return_value = project_dir
        project_dir.name = "EmptyProject"

        captured_output = io.StringIO()
        sys.stdout = captured_output

        run_onboard_logic(project_dir)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("Agent configuration file not found", output)
        self.assertIn("Git not found", output)
        self.assertIn("You are all caught up", output)


if __name__ == '__main__':
    unittest.main()
