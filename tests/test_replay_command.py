import unittest
import shutil
import subprocess
from pathlib import Path

class TestReplayCommand(unittest.TestCase):
    def setUp(self):
        self.log_dir = Path("agents/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.log_dir, ignore_errors=True)

    def test_replay_command(self):
        # Create a mock log file
        log_content = """2023-10-27 10:00:00 - INFO -
THOUGHTS:
This is a test thought.

COMMAND:
echo "This is a test command."
"""
        log_dir = Path("agents/logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "test_replay.log"
        log_file.write_text(log_content)

        # Run the replay command
        result = subprocess.run(
            ["./main.py", "replay", "test_replay"],
            capture_output=True,
            text=True,
            # Simulate pressing Enter once to advance to the next step, then 'q' to quit.
            input="\\nq\\n",
        )

        # Check the output
        self.assertIn("--- Agent Log Replay ---", result.stdout)
        self.assertIn("Run ID: test_replay", result.stdout)
        self.assertIn("Found 1 steps.", result.stdout)
        self.assertIn("This is a test thought.", result.stdout)
        self.assertIn("echo \"This is a test command.\"", result.stdout)

if __name__ == '__main__':
    unittest.main()
