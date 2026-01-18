import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import subprocess
import json

from shared.cli_utils import get_suggestions, _run_enhanced_status_logic, _parse_metrics

class TestCliUtils(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('shared.cli_utils.get_workflow_stage', return_value="IN_PROGRESS")
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=True)
    def test_get_suggestions_with_uncommitted_changes(self, mock_has_changes, mock_get_stage):
        suggestions = get_suggestions(self.project_dir)
        suggestion_commands = [s['command'] for s in suggestions]
        self.assertIn("main.py diff-summary", suggestion_commands)
        self.assertIn("main.py revert --interactive", suggestion_commands)

    @patch('shared.cli_utils.get_workflow_stage', return_value="COMPLETED")
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=False)
    def test_get_suggestions_for_completed_stage(self, mock_has_changes, mock_get_stage):
        suggestions = get_suggestions(self.project_dir)
        suggestion_commands = [s['command'] for s in suggestions]
        self.assertIn("main.py workflow advance", suggestion_commands)

    @patch('shared.cli_utils.get_workflow_stage', return_value="QA_PASSED")
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=False)
    def test_get_suggestions_for_qa_passed_stage(self, mock_has_changes, mock_get_stage):
        suggestions = get_suggestions(self.project_dir)
        suggestion_commands = [s['command'] for s in suggestions]
        self.assertIn("main.py workflow advance", suggestion_commands)

    @patch('shared.cli_utils.get_workflow_stage', return_value="SIGNED_OFF")
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=False)
    def test_get_suggestions_for_signed_off_stage(self, mock_has_changes, mock_get_stage):
        suggestions = get_suggestions(self.project_dir)
        suggestion_commands = [s['command'] for s in suggestions]
        self.assertIn("main.py clean --archive", suggestion_commands)

    @patch('shared.cli_utils.get_workflow_stage', return_value="IN_PROGRESS")
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=False)
    def test_get_suggestions_with_trash_items(self, mock_has_changes, mock_get_stage):
        trash_dir = self.project_dir / ".agent_trash"
        trash_dir.mkdir()
        (trash_dir / "some_file.txt").touch()
        suggestions = get_suggestions(self.project_dir)
        suggestion_commands = [s['command'] for s in suggestions]
        self.assertIn("main.py artifacts trash list", suggestion_commands)
        self.assertIn("main.py artifacts trash restore", suggestion_commands)

    @patch('shared.cli_utils.get_workflow_stage', return_value="IN_PROGRESS")
    @patch('shared.cli_utils._has_uncommitted_changes', return_value=False)
    def test_get_suggestions_with_run_id(self, mock_has_changes, mock_get_stage):
        (self.project_dir / ".agent_run_id").touch()
        suggestions = get_suggestions(self.project_dir)
        suggestion_commands = [s['command'] for s in suggestions]
        self.assertIn("main.py logs", suggestion_commands)

    def test_run_enhanced_status_logic_no_activity(self):
        """Test the enhanced status logic in a clean directory with no activity."""
        output = _run_enhanced_status_logic(self.project_dir)

        self.assertIn("--- Project Status:", output)
        self.assertIn("[ Workflow: In Progress ]", output)
        self.assertIn("[ Recent Activity ]", output)
        self.assertIn("No agent activity recorded.", output)
        self.assertIn("[ Recent File Changes ]", output)
        self.assertIn("Not a git repository.", output)
        self.assertIn("[ Next Steps ]", output)
        self.assertIn("✅ Project is in a clean state.", output)

    def test_run_enhanced_status_logic_with_history(self):
        """Test the enhanced status logic with a mock history file."""
        history_file = self.project_dir / ".agent_history"
        history_file.write_text("test-project-gemini-20231027120000\n"
                                "test-project-gemini-20231027120500\n")

        output = _run_enhanced_status_logic(self.project_dir)
        self.assertIn("2023-10-27 12:00:00 : Agent Run (test-project-gemini-20231027120000)", output)
        self.assertIn("2023-10-27 12:05:00 : Agent Run (test-project-gemini-20231027120500)", output)

    @patch('shared.cli_utils.shutil.which', return_value='/usr/bin/git')
    def test_run_enhanced_status_logic_with_git_changes(self, mock_which):
        """Test the enhanced status logic with uncommitted git changes."""
        # Setup a real git repo to test against
        subprocess.run(["git", "init"], cwd=self.project_dir, capture_output=True, check=True)
        (self.project_dir / ".git").mkdir(exist_ok=True)
        (self.project_dir / "test.txt").write_text("hello")
        subprocess.run(["git", "add", "test.txt"], cwd=self.project_dir, capture_output=True, check=True)
        (self.project_dir / "test.txt").write_text("hello world")

        output = _run_enhanced_status_logic(self.project_dir)
        self.assertIn("M test.txt", output)

    def test_run_enhanced_status_logic_completed_workflow(self):
        """Test the enhanced status logic for a completed workflow stage."""
        (self.project_dir / "COMPLETED").touch()
        output = _run_enhanced_status_logic(self.project_dir)
        self.assertIn("[ Workflow: Completed ]", output)
        self.assertIn("Advance the workflow to the 'QA Passed' stage", output)

    def test_run_enhanced_status_logic_with_feature_summary(self):
        """Test the enhanced status logic with a feature_list.json file."""
        feature_file = self.project_dir / "feature_list.json"
        feature_file.write_text(json.dumps(["feature 1", "feature 2", "feature 3", "feature 4"]))

        output = _run_enhanced_status_logic(self.project_dir)
        self.assertIn("Found 4 features in feature_list.json:", output)
        self.assertIn("- feature 1", output)
        self.assertIn("- feature 2", output)
        self.assertIn("- feature 3", output)
        self.assertIn("...", output)
        self.assertNotIn("- feature 4", output)

    def test_run_enhanced_status_logic_with_metrics(self):
        """Test the enhanced status logic displays metrics when the file exists."""
        metrics_file = self.project_dir / "final_metrics.txt"
        metrics_content = """
Total Execution Time (s): 123.45
Total Iterations: 10
Total Errors: 2
LLM Tokens Used: 5000
"""
        metrics_file.write_text(metrics_content)

        output = _run_enhanced_status_logic(self.project_dir)
        self.assertIn("[ Latest Run Metrics ]", output)
        self.assertIn("Run Time:     2m 3.45s", output)
        self.assertIn("Iterations:   10", output)
        self.assertIn("Errors:       2", output)
        self.assertIn("Tokens Used:  5000", output)

    def test_run_enhanced_status_logic_without_metrics(self):
        """Test the enhanced status logic handles a missing metrics file gracefully."""
        output = _run_enhanced_status_logic(self.project_dir)
        self.assertIn("[ Latest Run Metrics ]", output)
        self.assertIn("No metrics file found for the last run.", output)

    def test_parse_metrics_prometheus(self):
        """Test parsing Prometheus-style metrics."""
        metrics_file = self.project_dir / "prom_metrics.txt"
        metrics_file.write_text("""
# HELP llm_tokens_total Combined token counter
# TYPE llm_tokens_total counter
llm_tokens_total{agent_id="gemini_agent",model="gemini-1.5-pro",type="input"} 1000
llm_tokens_total{agent_id="gemini_agent",model="gemini-1.5-pro",type="output"} 500
# HELP agent_errors_total All agent errors
# TYPE agent_errors_total counter
agent_errors_total{error_type="log_error"} 2
# HELP agent_iterations_total Total iterations
# TYPE agent_iterations_total gauge
agent_iterations_total{project="test"} 5
        """.strip())

        metrics = _parse_metrics(metrics_file)
        self.assertEqual(metrics.get("LLM Tokens Used"), 1500)
        self.assertEqual(metrics.get("Model"), "gemini-1.5-pro")
        self.assertEqual(metrics.get("Total Errors"), 2)
        self.assertEqual(metrics.get("Total Iterations"), 5)
        self.assertEqual(metrics.get("llm_tokens_total__gemini-1.5-pro__input"), 1000)
        self.assertEqual(metrics.get("llm_tokens_total__gemini-1.5-pro__output"), 500)

if __name__ == '__main__':
    unittest.main()
