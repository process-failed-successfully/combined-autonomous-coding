import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import subprocess
import sys

class TestReplayCommand(unittest.TestCase):

    def setUp(self):
        self.repo_root = Path(__file__).parent.parent
        self.logs_dir = self.repo_root / "agents/logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.run_id = "test_replay_run"
        self.log_file = self.logs_dir / f"{self.run_id}.log"
        self.log_content = """
13:42:12 - INFO - Sending prompt to Gemini...
13:42:12 - DEBUG - Sending Augmented Prompt:
Thought 1
---
Action 1
13:42:12 - INFO - Sending prompt to Gemini...
13:42:12 - DEBUG - Sending Augmented Prompt:
Thought 2
---
Action 2
"""
        self.log_file.write_text(self.log_content)

    def tearDown(self):
        if self.log_file.exists():
            self.log_file.unlink()

    def test_replay_command(self):
        main_script_path = self.repo_root / "main.py"
        process = subprocess.Popen(
            [sys.executable, str(main_script_path), "replay", self.run_id],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Simulate user interaction
        process.stdin.write("\n")
        process.stdin.flush()
        process.stdin.write("q\n")
        process.stdin.flush()

        stdout, stderr = process.communicate()

        self.assertIn(f"--- Replaying run: {self.run_id} ---", stdout)
        self.assertIn("Found 2 steps.", stdout)
        self.assertIn("--- Step 1/2 ---", stdout)
        self.assertIn(">>> THOUGHT:", stdout)
        self.assertIn("Thought 1", stdout)
        self.assertIn(">>> ACTION:", stdout)
        self.assertIn("Action 1", stdout)
        self.assertIn("--- Step 2/2 ---", stdout)
        self.assertIn("Thought 2", stdout)
        self.assertIn("Action 2", stdout)
        self.assertIn("Exiting replay.", stdout)

if __name__ == '__main__':
    unittest.main()
