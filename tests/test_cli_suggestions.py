
import unittest
from unittest.mock import patch, MagicMock
import io
import sys
from main import get_parser, parse_args

class TestCLISuggestions(unittest.TestCase):

    def setUp(self):
        self.parser = get_parser()

    def test_suggest_status_for_stat(self):
        with self.assertRaises(SystemExit) as cm, \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            parse_args(self.parser, ['stat'])

        self.assertEqual(cm.exception.code, 2)
        output = mock_stderr.getvalue()
        self.assertIn("invalid choice: 'stat'", output)
        self.assertIn("Did you mean this?", output)
        self.assertIn("status", output)

    def test_suggest_history_for_hist(self):
        with self.assertRaises(SystemExit) as cm, \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            parse_args(self.parser, ['hist'])

        self.assertEqual(cm.exception.code, 2)
        output = mock_stderr.getvalue()
        self.assertIn("invalid choice: 'hist'", output)
        self.assertIn("Did you mean this?", output)
        self.assertIn("history", output)

    def test_no_suggestion_for_garbage(self):
        with self.assertRaises(SystemExit) as cm, \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            parse_args(self.parser, ['asdfghjkl'])

        self.assertEqual(cm.exception.code, 2)
        output = mock_stderr.getvalue()
        self.assertIn("invalid choice: 'asdfghjkl'", output)
        self.assertNotIn("Did you mean this?", output)

    def test_suggest_configure_for_configur(self):
        with self.assertRaises(SystemExit) as cm, \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            parse_args(self.parser, ['configur'])

        self.assertEqual(cm.exception.code, 2)
        output = mock_stderr.getvalue()
        self.assertIn("invalid choice: 'configur'", output)
        self.assertIn("Did you mean this?", output)
        self.assertIn("configure", output)

if __name__ == '__main__':
    unittest.main()
