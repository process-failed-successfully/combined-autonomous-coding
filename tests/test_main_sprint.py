import unittest
from unittest.mock import patch, MagicMock
import argparse
import json
from pathlib import Path
import tempfile
import shutil
import io

import main


class TestMainSprint(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.temp_dir)
        self.sprint_plan_path = self.project_dir / "sprint_plan.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _write_sprint_plan(self, data):
        with open(self.sprint_plan_path, 'w') as f:
            json.dump(data, f)

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_sprint_status_no_plan_file(self, mock_stderr):
        args = argparse.Namespace(
            command='sprint',
            action='status',
            project_dir=self.project_dir
        )
        with self.assertRaises(SystemExit) as cm:
            main.run_sprint_command(args)

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("sprint_plan.json not found", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_sprint_status_with_plan_file(self, mock_stdout):
        sprint_data = {
            "sprint_goal": "Implement the core feature",
            "tasks": [
                {"id": "task-1", "title": "Setup the database"},
                {"id": "task-2", "title": "Create the API"},
            ]
        }
        self._write_sprint_plan(sprint_data)
        args = argparse.Namespace(
            command='sprint',
            action='status',
            project_dir=self.project_dir
        )

        with self.assertRaises(SystemExit) as cm:
            with patch('subprocess.run', return_value=MagicMock(stdout='')):
                main.run_sprint_command(args)

        self.assertEqual(cm.exception.code, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Sprint Status", output)
        self.assertIn("Implement the core feature", output)
        self.assertIn("task-1", output)
        self.assertIn("Setup the database", output)
        self.assertIn("task-2", output)
        self.assertIn("Create the API", output)

    @patch('main._worktree_diff')
    def test_sprint_diff_action(self, mock_worktree_diff):
        args = argparse.Namespace(
            command='sprint',
            action='diff',
            task_id='task-123',
            project_dir=self.project_dir
        )
        main.run_sprint_command(args)
        mock_worktree_diff.assert_called_once()
        call_args = mock_worktree_diff.call_args[0]
        self.assertEqual(call_args[0].worktree_name, 'sprint-task-task-123')

    @patch('main._worktree_merge')
    def test_sprint_merge_action(self, mock_worktree_merge):
        args = argparse.Namespace(
            command='sprint',
            action='merge',
            task_id='task-456',
            project_dir=self.project_dir,
            clean=True,
            yes=True
        )
        main.run_sprint_command(args)
        mock_worktree_merge.assert_called_once()
        call_args = mock_worktree_merge.call_args[0]
        self.assertEqual(call_args[0].worktree_name, 'sprint-task-task-456')
