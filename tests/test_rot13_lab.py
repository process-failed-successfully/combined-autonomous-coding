import unittest
from unittest.mock import patch, MagicMock
from shared.rot13_lab import run_rot13_lab_logic

class TestRot13Lab(unittest.TestCase):

    @patch('sys.stdout')
    def test_run_rot13_lab_logic_with_arg(self, mock_stdout):
        args = MagicMock()
        args.text = "Hello World!"

        result = run_rot13_lab_logic(args)

        self.assertTrue(result)
        # "Hello World!" -> "Uryyb Jbeyq!"
        mock_stdout.write.assert_any_call("Uryyb Jbeyq!")

    @patch('sys.stdout')
    def test_run_rot13_lab_logic_decoding(self, mock_stdout):
        args = MagicMock()
        args.text = "Uryyb Jbeyq!"

        result = run_rot13_lab_logic(args)

        self.assertTrue(result)
        # "Uryyb Jbeyq!" -> "Hello World!"
        mock_stdout.write.assert_any_call("Hello World!")

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdin.read', return_value="Secret Message")
    @patch('sys.stdout')
    def test_run_rot13_lab_logic_with_stdin(self, mock_stdout, mock_read, mock_isatty):
        args = MagicMock()
        args.text = None

        result = run_rot13_lab_logic(args)

        self.assertTrue(result)
        # "Secret Message" -> "Frperg Zrffntr"
        mock_stdout.write.assert_any_call("Frperg Zrffntr")

    @patch('sys.stderr')
    def test_run_rot13_lab_logic_missing_input(self, mock_stderr):
        args = MagicMock()
        args.text = None

        with patch('sys.stdin.isatty', return_value=True):
            result = run_rot13_lab_logic(args)

        self.assertFalse(result)
        # Check that 'Error: Input text required (argument or stdin).\n' is written
        # Since write may be called multiple times, let's just check the arguments
        call_args = [call[0][0] for call in mock_stderr.write.call_args_list]
        self.assertTrue(any("Input text required" in arg for arg in call_args))

if __name__ == "__main__":
    unittest.main()
