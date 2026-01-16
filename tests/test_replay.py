
import unittest
from unittest.mock import patch, MagicMock
import subprocess
import sys
from pathlib import Path

class TestReplayCommand(unittest.TestCase):
    def test_replay_command_flow(self):
        # Create a dummy log file
        log_content = """2024-07-15 10:00:00,123 - INFO - Thinking:
First step.
2024-07-15 10:00:01,456 - INFO - Tool Call:
Second step.
"""
        log_dir = Path("agents/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        dummy_log_path = log_dir / "test_run.log"
        dummy_log_path.write_text(log_content)

        # Simulate user inputs: 'n' (next), 'p' (previous), 'j 2' (jump), 'q' (quit)
        user_inputs = ['n', 'p', 'j 2', 'q']

        # Use subprocess to run the main.py script with the replay command
        process = subprocess.Popen(
            [sys.executable, 'main.py', 'replay', 'test_run'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line-buffered
        )

        # Interaction part
        try:
            # First prompt, send 'n'
            process.stdin.write(user_inputs[0] + "\n")
            process.stdin.flush()

            # Second prompt, send 'p'
            process.stdin.write(user_inputs[1] + "\n")
            process.stdin.flush()

            # Third prompt, send 'j 2'
            process.stdin.write(user_inputs[2] + "\n")
            process.stdin.flush()

            # Fourth prompt, send 'q'
            process.stdin.write(user_inputs[3] + "\n")
            process.stdin.flush()

            # Now, get the output
            stdout, stderr = process.communicate(timeout=5)

        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            self.fail(f"Process timed out. STDOUT: {stdout}, STDERR: {stderr}")

        # Check for errors first
        self.assertEqual(stderr, '')

        # Check that the output contains the expected content from both steps
        self.assertIn("Step 1/2", stdout)
        self.assertIn("First step.", stdout)
        self.assertIn("Step 2/2", stdout)
        self.assertIn("Second step.", stdout)

        # Clean up the dummy log file
        dummy_log_path.unlink()

if __name__ == '__main__':
    unittest.main()
