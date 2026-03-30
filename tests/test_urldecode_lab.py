import unittest
import io
from unittest.mock import patch, MagicMock

from shared.urldecode_lab import run_urldecode_lab_logic


class TestUrldecodeLab(unittest.TestCase):
    def test_run_urldecode_lab_logic_success(self):
        args = MagicMock()
        args.text = "hello%20world"

        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            success = run_urldecode_lab_logic(args)

            self.assertTrue(success)
            self.assertEqual(mock_stdout.getvalue().strip(), "hello world")

    def test_run_urldecode_lab_logic_no_text(self):
        args = MagicMock()
        args.text = None

        with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            success = run_urldecode_lab_logic(args)

            self.assertFalse(success)
            self.assertIn("Error: No text specified", mock_stderr.getvalue())
