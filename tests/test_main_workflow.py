import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import io
import sys
from argparse import Namespace

# Add project root to path to allow direct import of main
sys.path.insert(0, str(Path(__file__).parent.parent))
import main as main_script


class TestWorkflowCommand(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir) / "test_project"
        self.project_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _run_workflow_command(self, action, yes=False):
        args = Namespace(
            command="workflow",
            action=action,
            project_dir=self.project_dir,
            yes=yes
        )
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                main_script.run_workflow(args)
            except SystemExit as e:
                # We expect sys.exit(0) on success
                self.assertEqual(e.code, 0)
            return mock_stdout.getvalue()

    def test_workflow_status_in_progress(self):
        output = self._run_workflow_command("status")
        self.assertIn("Current Stage: In Progress", output)
        self.assertIn("Next action: 'workflow advance' to move to 'Completed'", output)

    def test_workflow_status_completed(self):
        (self.project_dir / "COMPLETED").touch()
        output = self._run_workflow_command("status")
        self.assertIn("Current Stage: Completed", output)
        self.assertIn("Next action: 'workflow advance' to move to 'QA Passed'", output)

    def test_workflow_status_qa_passed(self):
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "QA_PASSED").touch()
        output = self._run_workflow_command("status")
        self.assertIn("Current Stage: QA Passed", output)
        self.assertIn("Next action: 'workflow advance' to move to 'Signed Off'", output)

    def test_workflow_status_signed_off(self):
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "QA_PASSED").touch()
        (self.project_dir / "PROJECT_SIGNED_OFF").touch()
        output = self._run_workflow_command("status")
        self.assertIn("Current Stage: Signed Off", output)
        self.assertIn("Project is complete. No further workflow actions.", output)

    @patch('builtins.input', return_value='y')
    def test_workflow_advance_from_in_progress_with_confirm(self, mock_input):
        output = self._run_workflow_command("advance")
        self.assertTrue((self.project_dir / "COMPLETED").exists())
        self.assertIn("Successfully advanced workflow to 'Completed'", output)
        mock_input.assert_called_once()

    def test_workflow_advance_from_qa_passed_with_yes_flag(self):
        (self.project_dir / "COMPLETED").touch()
        (self.project_dir / "QA_PASSED").touch()
        output = self._run_workflow_command("advance", yes=True)
        self.assertTrue((self.project_dir / "PROJECT_SIGNED_OFF").exists())
        self.assertIn("Successfully advanced workflow to 'Signed Off'", output)

    def test_workflow_advance_at_final_stage(self):
        (self.project_dir / "PROJECT_SIGNED_OFF").touch()
        output = self._run_workflow_command("advance", yes=True)
        self.assertIn("Project is already at the final 'Signed Off' stage", output)

    @patch('builtins.input', return_value='n')
    def test_workflow_advance_aborted(self, mock_input):
        output = self._run_workflow_command("advance")
        self.assertFalse((self.project_dir / "COMPLETED").exists())
        self.assertIn("Aborted", output)

    @patch('builtins.input', return_value='y')
    def test_workflow_revert_from_completed_with_confirm(self, mock_input):
        (self.project_dir / "COMPLETED").touch()
        output = self._run_workflow_command("revert")
        self.assertFalse((self.project_dir / "COMPLETED").exists())
        self.assertIn("Successfully reverted workflow to 'In Progress'", output)
        mock_input.assert_called_once()

    def test_workflow_revert_from_signed_off_with_yes_flag(self):
        (self.project_dir / "PROJECT_SIGNED_OFF").touch()
        output = self._run_workflow_command("revert", yes=True)
        self.assertFalse((self.project_dir / "PROJECT_SIGNED_OFF").exists())
        self.assertIn("Successfully reverted workflow to 'QA Passed'", output)

    def test_workflow_revert_at_initial_stage(self):
        output = self._run_workflow_command("revert", yes=True)
        self.assertIn("Project is already at the initial 'In Progress' stage", output)

    @patch('builtins.input', return_value='n')
    def test_workflow_revert_aborted(self, mock_input):
        (self.project_dir / "COMPLETED").touch()
        output = self._run_workflow_command("revert")
        self.assertTrue((self.project_dir / "COMPLETED").exists())
        self.assertIn("Aborted", output)

    def test_get_workflow_stage_logic(self):
        from shared.cli_utils import get_workflow_stage
        # Test In Progress
        self.assertEqual(get_workflow_stage(self.project_dir), "IN_PROGRESS")
        # Test Completed
        (self.project_dir / "COMPLETED").touch()
        self.assertEqual(get_workflow_stage(self.project_dir), "COMPLETED")
        # Test QA Passed (should override Completed)
        (self.project_dir / "QA_PASSED").touch()
        self.assertEqual(get_workflow_stage(self.project_dir), "QA_PASSED")
        # Test Signed Off (should override everything)
        (self.project_dir / "PROJECT_SIGNED_OFF").touch()
        self.assertEqual(get_workflow_stage(self.project_dir), "SIGNED_OFF")


if __name__ == '__main__':
    unittest.main()