import unittest
from unittest.mock import patch
import sys
import io
import asyncio
from main import parse_args, main


class TestMainVersion(unittest.TestCase):

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_version_flag(self, mock_stdout):
        with patch.object(sys, "argv", ["main.py", "--version"]):
            with self.assertRaises(SystemExit) as cm:
                parse_args()
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("1.0.0", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_version_subcommand(self, mock_stdout):
        with patch.object(sys, "argv", ["main.py", "version"]):
            with self.assertRaises(SystemExit) as cm:
                asyncio.run(main())
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("Combined Autonomous Coding Agent v1.0.0", mock_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
