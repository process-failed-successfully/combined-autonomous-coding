import unittest
from unittest.mock import patch, MagicMock
import io

from shared.codec_lab import run_codec_lab_logic

class TestCodecLabCLI(unittest.TestCase):
    @patch("sys.exit")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_base64_encode(self, mock_stdout, mock_exit):
        args = MagicMock()
        args.algorithm = "base64"
        args.mode = "encode"
        args.text = "Hello"

        run_codec_lab_logic(args)

        # mock_exit shouldn't be called on success (because the original function doesn't call sys.exit(0) at the end)
        mock_exit.assert_not_called()
        self.assertEqual(mock_stdout.getvalue().strip(), "SGVsbG8=")

    @patch("sys.exit")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_base64_decode(self, mock_stdout, mock_exit):
        args = MagicMock()
        args.algorithm = "base64"
        args.mode = "decode"
        args.text = "SGVsbG8="

        run_codec_lab_logic(args)

        mock_exit.assert_not_called()
        self.assertEqual(mock_stdout.getvalue().strip(), "Hello")

    @patch("sys.exit")
    @patch("sys.stdout", new_callable=io.StringIO)
    def test_cli_url_encode(self, mock_stdout, mock_exit):
        args = MagicMock()
        args.algorithm = "url"
        args.mode = "encode"
        args.text = "Hello World?"

        run_codec_lab_logic(args)

        mock_exit.assert_not_called()
        self.assertEqual(mock_stdout.getvalue().strip(), "Hello%20World%3F")

    @patch("sys.exit")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_cli_invalid_algorithm(self, mock_stderr, mock_exit):
        args = MagicMock()
        args.algorithm = "unknown_algo"
        args.mode = "encode"
        args.text = "Hello"

        run_codec_lab_logic(args)

        mock_exit.assert_called_once_with(1)
        self.assertIn("Unknown algorithm: unknown_algo", mock_stderr.getvalue())

    @patch("sys.exit")
    @patch("sys.stderr", new_callable=io.StringIO)
    def test_cli_no_input(self, mock_stderr, mock_exit):
        args = MagicMock()
        args.algorithm = "base64"
        args.mode = "encode"
        args.text = None

        with patch("sys.stdin.isatty", return_value=True):
            run_codec_lab_logic(args)

        mock_exit.assert_called_once_with(1)
        self.assertIn("Error: Input text required", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
