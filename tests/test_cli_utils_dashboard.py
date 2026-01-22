
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import shutil

from shared.cli_utils import _run_dashboard_logic


class TestCliUtilsDashboard(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the project
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.project_dir)

    @patch('shared.cli_utils.get_workflow_stage')
    @patch('shared.cli_utils.get_suggestions')
    @patch('shutil.which')
    def test_dashboard_logic_no_git(self, mock_which, mock_get_suggestions, mock_get_workflow_stage):
        # Arrange
        mock_get_workflow_stage.return_value = "IN_PROGRESS"
        mock_get_suggestions.return_value = []
        mock_which.return_value = None  # Simulate git not being installed

        # Act
        output = _run_dashboard_logic(self.project_dir)

        # Assert
        self.assertIn("--- Project Dashboard: test_project ---", output)
        self.assertIn("Status: In Progress", output)
        self.assertIn("Not a git repository.", output)
        self.assertIn("No agent runs recorded.", output)
        self.assertIn("Project is in a clean state.", output)

    @patch('shared.cli_utils.get_workflow_stage')
    @patch('shared.cli_utils.get_suggestions')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_dashboard_logic_clean_git(self, mock_subprocess_run, mock_which, mock_get_suggestions, mock_get_workflow_stage):
        # Arrange
        mock_get_workflow_stage.return_value = "IN_PROGRESS"
        mock_get_suggestions.return_value = []
        mock_which.return_value = '/usr/bin/git'
        (self.project_dir / ".git").mkdir()

        # Mock git branch command
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="main", returncode=0, stderr=""),
            MagicMock(stdout="", returncode=0, stderr="")
        ]

        # Act
        output = _run_dashboard_logic(self.project_dir)

        # Assert
        self.assertIn("Branch: main", output)
        self.assertIn("Status: ✅ Clean", output)

    @patch('shared.cli_utils.get_workflow_stage')
    @patch('shared.cli_utils.get_suggestions')
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_dashboard_logic_with_changes(self, mock_subprocess_run, mock_which, mock_get_suggestions, mock_get_workflow_stage):
        # Arrange
        mock_get_workflow_stage.return_value = "IN_PROGRESS"
        mock_get_suggestions.return_value = []
        mock_which.return_value = '/usr/bin/git'
        (self.project_dir / ".git").mkdir()

        # Mock git commands
        mock_subprocess_run.side_effect = [
            MagicMock(stdout="feature-branch", returncode=0, stderr=""),
            MagicMock(stdout=" M my_file.py", returncode=0, stderr="")
        ]

        # Act
        output = _run_dashboard_logic(self.project_dir)

        # Assert
        self.assertIn("Branch: feature-branch", output)
        self.assertIn("Status: ⚠️ Uncommitted changes", output)

    @patch('shared.cli_utils.get_workflow_stage')
    @patch('shared.cli_utils.get_suggestions')
    @patch('shutil.which')
    def test_dashboard_logic_no_history(self, mock_which, mock_get_suggestions, mock_get_workflow_stage):
        # Arrange
        mock_get_workflow_stage.return_value = "IN_PROGRESS"
        mock_get_suggestions.return_value = []
        mock_which.return_value = None

        # Act
        output = _run_dashboard_logic(self.project_dir)

        # Assert
        self.assertIn("No agent runs recorded.", output)

    @patch('shared.cli_utils._find_metrics_file')
    @patch('shared.cli_utils._parse_metrics')
    @patch('shared.cli_utils.get_workflow_stage')
    @patch('shared.cli_utils.get_suggestions')
    @patch('shutil.which')
    def test_dashboard_logic_with_history_and_metrics(self, mock_which, mock_get_suggestions, mock_get_workflow_stage, mock_parse_metrics, mock_find_metrics_file):
        # Arrange
        mock_get_workflow_stage.return_value = "IN_PROGRESS"
        mock_get_suggestions.return_value = []
        mock_which.return_value = None

        # Create a dummy history file
        history_file = self.project_dir / ".agent_history"
        history_file.write_text("run-1234\n")

        mock_find_metrics_file.return_value = self.project_dir / "final_metrics.txt"
        mock_parse_metrics.return_value = {
            "Total Execution Time (s)": 123.45,
            "Total Iterations": 5,
            "Total Errors": 1
        }

        # Act
        output = _run_dashboard_logic(self.project_dir)

        # Assert
        self.assertIn("Run ID: run-1234", output)
        self.assertIn("Execution Time: 2m 3.45s", output)
        self.assertIn("Iterations:     5", output)
        self.assertIn("Errors:         1", output)


if __name__ == '__main__':
    unittest.main()
