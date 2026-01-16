import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from main import run_replay
from shared.log_parser import LogStep

class TestReplayCommand(unittest.TestCase):
    @patch('builtins.input', side_effect=['', 'q'])
    @patch('sys.stdout')
    @patch('main.parse_log_file')
    def test_replay_command(self, mock_parse_log_file, mock_stdout, mock_input):
        # 1. Create mock log steps
        mock_steps = [
            LogStep(
                timestamp="2023-10-27 10:00:00",
                thoughts="This is a test thought.",
                command='echo "This is a test command."',
                files=None,
                stdout=None,
                diff=None
            )
        ]

        # 2. Configure the mock to return the steps
        mock_parse_log_file.return_value = mock_steps

        # 3. Set up arguments for run_replay
        args = MagicMock()
        args.project_dir = Path(".")
        args.run_id = "test_replay"

        # 4. Run the replay command function
        with self.assertRaises(SystemExit) as cm:
            run_replay(args)

        self.assertEqual(cm.exception.code, 0)

        # 5. Check the output
        output = "".join(call.args[0] for call in mock_stdout.write.call_args_list)

        self.assertIn("--- Agent Log Replay ---", output)
        self.assertIn("Run ID: test_replay", output)
        self.assertIn("Found 1 steps.", output)
        self.assertIn("This is a test thought.", output)
        self.assertIn('echo "This is a test command."', output)

if __name__ == '__main__':
    unittest.main()
