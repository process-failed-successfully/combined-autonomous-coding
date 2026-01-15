
import unittest
from unittest.mock import patch, MagicMock
import subprocess
from pathlib import Path
import sys
import os
import tempfile
import shutil
import json

# Add the root directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from main import run_replay

class TestReplayCommand(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_project_dir = Path(self.temp_dir) / "test_project"
        self.test_project_dir.mkdir()

        # Mock the agents/logs directory inside the temporary directory structure
        # to ensure the test is isolated and doesn't write to the real project.
        self.repo_root_mock = Path(self.temp_dir) / "repo"
        self.logs_dir_mock = self.repo_root_mock / "agents/logs"
        self.logs_dir_mock.mkdir(parents=True, exist_ok=True)

        self.run_id = "test-run-123"
        self.log_file = self.logs_dir_mock / f"{self.run_id}.log"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("main.Path")
    @patch("subprocess.run")
    def test_replay_with_overrides(self, mock_subprocess_run, mock_path):
        # 1. Create a mock log file with the new JSON config format
        config_data = {
            "project_dir": ".",
            "agent_type": "gemini",
            "model": "gemini-1.0-pro",
            "max_iterations": 10,
            "verbose": False,
            "spec_file": "app_spec.txt",
            "agent_id": "some-agent-id", # This should be ignored by replay
        }
        config_line = f"2023-11-20 10:00:00,000 - INFO - Effective Config: {json.dumps(config_data)}\n"
        self.log_file.write_text(config_line)

        # Mock Path(__file__).parent to return our mocked repo root
        mock_path.return_value.parent = self.repo_root_mock

        # 2. Prepare the arguments for run_replay
        # Simulates: `main.py replay test-run-123 --project-dir <temp_dir>/test_project --model gemini-1.5-pro --verbose`
        args = MagicMock()
        args.run_id = self.run_id
        args.project_dir = self.test_project_dir
        args.replay_args = ["--model", "gemini-1.5-pro", "--verbose"]

        # 3. Configure the mock to return a successful exit code
        mock_subprocess_run.return_value.returncode = 0

        # 4. Call the function and catch SystemExit
        with self.assertRaises(SystemExit) as cm:
            run_replay(args)

        # 5. Assert that the subprocess was called with the correct, merged arguments
        self.assertTrue(mock_subprocess_run.called)

        call_args, _ = mock_subprocess_run.call_args
        called_command = call_args[0]

        # Expected command structure
        expected_executable = sys.executable
        expected_script = os.path.abspath("main.py")

        self.assertEqual(called_command[0], expected_executable)
        self.assertEqual(called_command[1], expected_script)

        # Use a dictionary to check for flags and their values for easier debugging
        command_dict = {}
        i = 2
        while i < len(called_command):
            arg = called_command[i]
            if arg.startswith("--"):
                if i + 1 < len(called_command) and not called_command[i+1].startswith("--"):
                    command_dict[arg] = called_command[i+1]
                    i += 2
                else:
                    command_dict[arg] = None # Flag without value
                    i += 1
            else:
                i += 1 # Should not happen if args are well-formed, but good for safety

        # Check for original arguments from the log file
        self.assertEqual(command_dict.get("--agent"), "gemini")
        self.assertEqual(command_dict.get("--max-iterations"), "10")
        self.assertEqual(command_dict.get("--spec"), "app_spec.txt")

        # Check for overridden arguments
        self.assertEqual(command_dict.get("--model"), "gemini-1.5-pro")

        # Check for new arguments that were not in the original
        self.assertIn("--verbose", command_dict)

        # Check that the project directory is correctly passed from the replay command, not the log
        self.assertEqual(command_dict.get("--project-dir"), str(self.test_project_dir))

        # Check that internal/derived fields are NOT passed
        self.assertNotIn("--agent-id", command_dict)

        # Check that the exit code is what the subprocess would have returned
        self.assertEqual(cm.exception.code, 0)

if __name__ == "__main__":
    unittest.main()
