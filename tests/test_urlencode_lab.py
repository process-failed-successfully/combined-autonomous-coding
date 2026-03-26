import unittest
from unittest.mock import MagicMock, patch
import io
from shared.urlencode_lab import run_urlencode_lab_logic


class TestUrlEncodeLabLogic(unittest.TestCase):

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_encode(self, mock_stdout):
        args = MagicMock()
        args.encode = "hello world/&?"
        args.decode = None

        result = run_urlencode_lab_logic(args)

        self.assertTrue(result)
        self.assertEqual(mock_stdout.getvalue().strip(), "hello%20world/%26%3F")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_decode(self, mock_stdout):
        args = MagicMock()
        args.encode = None
        args.decode = "hello%20world%2F%26%3F"

        result = run_urlencode_lab_logic(args)

        self.assertTrue(result)
        self.assertEqual(mock_stdout.getvalue().strip(), "hello world/&?")

    @patch('sys.stderr', new_callable=io.StringIO)
    def test_run_no_action(self, mock_stderr):
        args = MagicMock()
        args.encode = None
        args.decode = None

        result = run_urlencode_lab_logic(args)

        self.assertFalse(result)
        self.assertIn("Error: No action specified", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()
