import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_debug

class TestMainDebug(unittest.IsolatedAsyncioTestCase):

    @patch("main.run_debug_logic")
    async def test_run_debug_command_success(self, mock_run_logic):
        # Setup
        mock_run_logic.return_value = True

        args = argparse.Namespace(
            command_to_debug="echo 'hello'",
            project_dir=Path("."),
            agent="gemini",
            model=None,
            verbose=False
        )

        # Execute
        with self.assertRaises(SystemExit) as cm:
            await run_debug(args)

        # Verify
        self.assertEqual(cm.exception.code, 0)
        mock_run_logic.assert_called_once_with(
            command="echo 'hello'",
            project_dir=Path("."),
            agent_type="gemini",
            model=None,
            verbose=False
        )

    @patch("main.run_debug_logic")
    async def test_run_debug_command_failure(self, mock_run_logic):
        # Setup
        mock_run_logic.return_value = False # Command failed

        args = argparse.Namespace(
            command_to_debug="fail",
            project_dir=Path("."),
            agent="gemini",
            model=None,
            verbose=False
        )

        # Execute
        with self.assertRaises(SystemExit) as cm:
            await run_debug(args)

        # Verify
        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
