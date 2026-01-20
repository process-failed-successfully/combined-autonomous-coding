import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import sys
import os
import io

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.resolve import run_resolve_logic

class TestResolve(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")

    @patch("shared.resolve.scan_todos")
    async def test_no_todos(self, mock_scan):
        mock_scan.return_value = []

        # Capture stdout
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = await run_resolve_logic(self.project_dir, interactive=False)

        self.assertTrue(result)
        self.assertIn("No TODOs found", mock_stdout.getvalue())

    @patch("shared.resolve.scan_todos")
    @patch("builtins.input")
    @patch("shared.resolve.RefactorManager")
    async def test_resolve_interactive(self, MockRefactorManager, mock_input, mock_scan):
        # Setup mocks
        mock_scan.return_value = [
            {"file": "test.py", "line": 10, "tag": "TODO", "text": "Fix this bug"}
        ]

        # Mock user input: select 1, then confirm 'y'
        mock_input.side_effect = ["1", "y"]

        # Mock RefactorManager
        mock_manager_instance = MockRefactorManager.return_value
        mock_manager_instance.refactor_file = AsyncMock(return_value={
            "changed": True,
            "diff": "diff output",
            "new_content": "new code"
        })

        # Run
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            result = await run_resolve_logic(self.project_dir, interactive=True)

        self.assertTrue(result)

        # Verify interactions
        mock_scan.assert_called_once()
        mock_input.assert_called() # At least once

        # Verify instruction passed to agent
        call_args = mock_manager_instance.refactor_file.call_args
        self.assertIsNotNone(call_args)
        kwargs = call_args.kwargs
        instruction = kwargs['instruction']
        self.assertIn("Implement the following task", instruction)
        self.assertIn("Fix this bug", instruction)
        self.assertIn("remove the TODO", instruction)

        # Verify apply_changes called
        mock_manager_instance.apply_changes.assert_called_once()

    @patch("shared.resolve.scan_todos")
    @patch("builtins.input")
    @patch("shared.resolve.RefactorManager")
    async def test_resolve_abort(self, MockRefactorManager, mock_input, mock_scan):
        mock_scan.return_value = [
            {"file": "test.py", "line": 10, "tag": "TODO", "text": "Fix this"}
        ]
        # Mock user input: abort (empty string)
        mock_input.side_effect = [""]

        result = await run_resolve_logic(self.project_dir, interactive=True)
        self.assertTrue(result) # Abort is considered a "successful exit" of logic usually

        # Manager should not be instantiated or called
        MockRefactorManager.assert_not_called()

if __name__ == '__main__':
    unittest.main()
