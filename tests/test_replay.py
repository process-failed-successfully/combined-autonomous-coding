import unittest
import os
import time
from pathlib import Path
import tempfile
from shared.replay import ReplayManager


class TestReplayManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.test_dir.name)
        # Create agents/logs directory structure
        self.logs_dir = self.project_dir / "agents/logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.manager = ReplayManager(self.project_dir)

    def tearDown(self):
        self.test_dir.cleanup()

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
        log_path = self.logs_dir / "test_run.log"
        log_path.write_text(log_content, encoding="utf-8")

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
        log_path = self.logs_dir / "multi_turn.log"
        log_path.write_text(log_content, encoding="utf-8")

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

    def test_load_run_latest(self):
        # Create two log files with different timestamps
        log1 = self.logs_dir / "run1.log"
        log1.touch()
        # Set mtime to 100 seconds ago
        os.utime(log1, (time.time() - 100, time.time() - 100))

        log2 = self.logs_dir / "run2.log"
        log2.touch()
        os.utime(log2, (time.time(), time.time()))

        # ReplayManager looks for logs in project_dir/agents/logs
        # which we set up in setUp

        latest = self.manager.load_run()
        self.assertEqual(latest.name, "run2.log")

        # Test loading specific run
        specific = self.manager.load_run("run1")
        self.assertEqual(specific.name, "run1.log")


if __name__ == "__main__":
    unittest.main()
