import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from shared.replay import ReplayManager, Turn, Action

class TestReplayManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = ReplayManager(self.project_dir)

    def test_parse_log(self):
        log_content = """10:00:00 - INFO - Sending prompt to Gemini...
10:00:01 - INFO - Received response from Gemini.
10:00:01 - DEBUG - Response:
Thinking process...
10:00:02 - INFO - Processing response blocks...
10:00:03 - INFO - [Executing Bash] ls -la
10:00:04 - INFO - [Output] total 0
drwxr-xr-x 2 user user 64 Jan 1 00:00 .
"""
        # Create a temporary log file
        with patch.object(Path, 'read_text', return_value=log_content):
            log_path = MagicMock(spec=Path)
            log_path.read_text.return_value = log_content

            turns = self.manager.parse_log(log_path)

            self.assertEqual(len(turns), 1)
            turn = turns[0]
            self.assertEqual(turn.turn_id, 1)
            self.assertEqual(turn.timestamp, "10:00:00")
            self.assertIn("Thinking process...", turn.thought)
            self.assertEqual(len(turn.actions), 1)
            action = turn.actions[0]
            self.assertEqual(action.command, "ls -la")
            self.assertIn("total 0", action.output)

    def test_parse_log_multi_turn(self):
        log_content = """10:00:00 - INFO - Sending prompt to Gemini...
10:00:01 - DEBUG - Response:
Thinking turn 1...
10:00:02 - INFO - [Executing Bash] echo 1
10:00:03 - INFO - [Output] 1
10:00:05 - INFO - Sending prompt to Gemini...
10:00:06 - DEBUG - Response:
Thinking turn 2...
10:00:07 - INFO - [Executing Bash] echo 2
10:00:08 - INFO - [Output] 2
"""
        with patch.object(Path, 'read_text', return_value=log_content):
            log_path = MagicMock(spec=Path)
            log_path.read_text.return_value = log_content

            turns = self.manager.parse_log(log_path)

            self.assertEqual(len(turns), 2)

            # Turn 1
            t1 = turns[0]
            self.assertIn("Thinking turn 1", t1.thought)
            self.assertEqual(len(t1.actions), 1)
            self.assertEqual(t1.actions[0].output.strip(), "1")
            # Verify thought didn't leak into output
            self.assertNotIn("Thinking turn 2", t1.actions[0].output)

            # Turn 2
            t2 = turns[1]
            self.assertIn("Thinking turn 2", t2.thought)
            self.assertEqual(len(t2.actions), 1)
            self.assertEqual(t2.actions[0].output.strip(), "2")
            # Verify output from turn 1 didn't leak into turn 2 thought
            self.assertNotIn("1", t2.thought)

    @patch("shared.replay.ReplayManager._find_logs_dir")
    def test_load_run_latest(self, mock_find):
        mock_logs_dir = MagicMock()
        mock_find.return_value = mock_logs_dir
        self.manager.logs_dir = mock_logs_dir

        log1 = MagicMock()
        log1.stat().st_mtime = 100
        log1.name = "run1.log"

        log2 = MagicMock()
        log2.stat().st_mtime = 200
        log2.name = "run2.log"

        mock_logs_dir.glob.return_value = [log1, log2]

        latest = self.manager.load_run()
        self.assertEqual(latest, log2)

if __name__ == "__main__":
    unittest.main()
