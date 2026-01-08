import unittest
from unittest.mock import patch
import io
import sys

from main import run_completion

class TestMainCompletion(unittest.TestCase):
    @patch('main.argcomplete')
    def test_completion_subcommand_outputs_shellcode(self, mock_argcomplete):
        # Arrange
        expected_shellcode = "# bash completion script"
        mock_argcomplete.shellcode.return_value = expected_shellcode

        # Act
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            with self.assertRaises(SystemExit) as cm:
                run_completion()

        # Assert
        self.assertEqual(cm.exception.code, 0)
        self.assertIn(expected_shellcode, mock_stdout.getvalue())

    @patch('main.argcomplete', None)
    def test_completion_subcommand_no_argcomplete(self):
        # Act
        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            with self.assertRaises(SystemExit) as cm:
                run_completion()

        # Assert
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("argcomplete is not installed", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
