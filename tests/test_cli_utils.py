import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from shared.cli_utils import get_suggestions

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

if __name__ == '__main__':
    unittest.main()
