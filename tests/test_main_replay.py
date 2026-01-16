
import unittest
from unittest.mock import patch, MagicMock, call
import subprocess
from pathlib import Path
import json
import asyncio
from main import run_replay
import argparse

class TestReplayCommand(unittest.TestCase):

    @patch('main.shutil.which')
    @patch('main.subprocess.run')
    @patch('main.run_gemini')
    @patch('main.setup_logger')
    def test_replay_successful(self, mock_setup_logger, mock_run_gemini, mock_subprocess_run, mock_shutil_which):
        # Arrange
        mock_shutil_which.return_value = '/usr/bin/git'
        mock_logger = MagicMock()
        mock_setup_logger.return_value = (mock_logger, MagicMock())

        # Mock git reset and clean to succeed
        mock_subprocess_run.return_value = MagicMock(returncode=0)

        # Create a dummy log file
        log_dir = Path("./agents/logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "test_run_id.log"
        log_content = """
2023-01-01 12:00:00,000 - INFO - Initial commit hash: abcdef123456
2023-01-01 12:00:01,000 - INFO - Initial configuration:
{
  "agent_type": "gemini",
  "project_dir": ".",
  "spec_file": "spec.txt"
}
"""
        log_file.write_text(log_content)

        args = argparse.Namespace(run_id="test_run_id", project_dir=Path("."), yes=True)

        # Act
        with self.assertRaises(SystemExit) as cm:
            asyncio.run(run_replay(args))

        # Assert
        self.assertEqual(cm.exception.code, 0) # Should exit cleanly

        # Verify git reset was called
        project_dir_abs = str(Path(".").resolve())
        expected_calls = [
            call(['/usr/bin/git', '-C', project_dir_abs, 'reset', '--hard', 'abcdef123456'], check=True, capture_output=True),
            call(['/usr/bin/git', '-C', project_dir_abs, 'clean', '-fdx'], check=True, capture_output=True)
        ]
        mock_subprocess_run.assert_has_calls(expected_calls)

        # Verify agent was called with correct config
        mock_run_gemini.assert_called_once()
        call_args, _ = mock_run_gemini.call_args
        replay_config = call_args[0]
        self.assertEqual(replay_config.agent_type, "gemini")
        self.assertEqual(replay_config.spec_file, Path("spec.txt"))
        self.assertTrue(replay_config.agent_id.startswith("replay-test_run_id-"))

        # Clean up
        log_file.unlink()

if __name__ == '__main__':
    unittest.main()
