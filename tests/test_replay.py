import unittest
from unittest.mock import patch, MagicMock
from shared.log_parser import parse_log_file, ReplayStep

class TestReplay(unittest.TestCase):
    def test_parse_log_file_multiple_steps(self):
        log_content = """
--- THOUGHT ---
This is the first thought.
--- COMMAND ---
ls -l
--- OUTPUT ---
total 0
--- THOUGHT ---
This is the second thought, with no command.
--- GIT DIFF ---
--- a/file.txt
+++ b/file.txt
@@ -1 +1 @@
-old
+new
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 2)

        # First step
        self.assertEqual(steps[0].thought, "This is the first thought.")
        self.assertEqual(steps[0].command, "ls -l")
        self.assertEqual(steps[0].output, "total 0")
        self.assertEqual(steps[0].diff, "")
        self.assertEqual(steps[0].commit_hash, "")

        # Second step
        self.assertEqual(steps[1].thought, "This is the second thought, with no command.")
        self.assertEqual(steps[1].command, "")
        self.assertEqual(steps[1].output, "")
        self.assertIn("-old", steps[1].diff)
        self.assertIn("+new", steps[1].diff)
        self.assertEqual(steps[1].commit_hash, "")

    def test_parse_log_file_empty_sections(self):
        log_content = """
--- THOUGHT ---
--- COMMAND ---
--- OUTPUT ---
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 1)
        step = steps[0]
        self.assertEqual(step.thought, "")
        self.assertEqual(step.command, "")
        self.assertEqual(step.output, "")

    @patch('builtins.input', side_effect=['n', 'p', 'q'])
    @patch('sys.stdout', new_callable=MagicMock)
    @patch('main.Path')
    def test_run_replay_interactive(self, mock_path_class, mock_stdout, mock_input):
        mock_log_file = MagicMock()
        mock_log_file.exists.return_value = True
        mock_log_file.read_text.return_value = """
--- THOUGHT ---
Step 1
--- COMMAND ---
echo "Step 1"
--- THOUGHT ---
Step 2
"""
        mock_path_class.return_value.parent.__truediv__.return_value = mock_log_file

        from main import run_replay
        args = MagicMock()
        args.run_id = "test_run"

        with self.assertRaises(SystemExit) as cm:
            run_replay(args)
        self.assertEqual(cm.exception.code, 0)

        mock_log_file.read_text.assert_called_once()
        self.assertEqual(mock_input.call_count, 3)

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('main.Path')
    def test_run_replay_file_not_found(self, mock_path_class, mock_stdout):
        mock_log_file = MagicMock()
        mock_log_file.exists.return_value = False
        mock_path_class.return_value.parent.__truediv__.return_value = mock_log_file

        from main import run_replay
        args = MagicMock()
        args.run_id = "test_run"

        with self.assertRaises(SystemExit) as cm:
            run_replay(args)
        self.assertEqual(cm.exception.code, 1)

if __name__ == "__main__":
    unittest.main()
