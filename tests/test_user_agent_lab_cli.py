import unittest
from unittest.mock import MagicMock, patch
import io
import sys
import argparse
from shared.user_agent_lab import run_user_agent_lab_logic

class TestUserAgentLabCLI(unittest.TestCase):
    def setUp(self):
        self.mock_stdout = io.StringIO()
        self.patcher = patch('sys.stdout', self.mock_stdout)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_parse_action(self):
        args = argparse.Namespace(
            action="parse",
            ua_string="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0 Safari/537.36",
            os=None, browser=None, version=None, project_dir=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_user_agent_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = self.mock_stdout.getvalue()
        self.assertIn("Browser: Chrome", output)
        self.assertIn("Os: Windows", output)
        self.assertIn("Version: 99.0", output)

    def test_parse_action_missing_arg(self):
        args = argparse.Namespace(
            action="parse",
            ua_string=None,
            os=None, browser=None, version=None, project_dir=None
        )
        with self.assertRaises(SystemExit) as cm:
            # We expect it to exit with 1 because ua_string is missing
            # We mock stderr to avoid cluttering test output
            with patch('sys.stderr', new=io.StringIO()):
                run_user_agent_lab_logic(args)

        self.assertEqual(cm.exception.code, 1)

    def test_generate_action(self):
        args = argparse.Namespace(
            action="generate",
            ua_string=None,
            os="Windows",
            browser="Chrome",
            version="100.0",
            project_dir=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_user_agent_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = self.mock_stdout.getvalue().strip()
        self.assertIn("Windows NT 10.0", output)
        self.assertIn("Chrome/100.0", output)

    def test_generate_action_missing_args(self):
        args = argparse.Namespace(
            action="generate",
            ua_string=None,
            os="Windows",
            browser=None, # Missing browser
            version="100.0",
            project_dir=None
        )
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new=io.StringIO()):
                run_user_agent_lab_logic(args)

        self.assertEqual(cm.exception.code, 1)

    def test_generate_action_invalid_args(self):
        args = argparse.Namespace(
            action="generate",
            ua_string=None,
            os="InvalidOS",
            browser="Chrome",
            version="100.0",
            project_dir=None
        )
        with self.assertRaises(SystemExit) as cm:
            with patch('sys.stderr', new=io.StringIO()):
                run_user_agent_lab_logic(args)

        self.assertEqual(cm.exception.code, 1)

    def test_list_action(self):
        args = argparse.Namespace(
            action="list",
            ua_string=None,
            os=None, browser=None, version=None, project_dir=None
        )
        with self.assertRaises(SystemExit) as cm:
            run_user_agent_lab_logic(args)

        self.assertEqual(cm.exception.code, 0)
        output = self.mock_stdout.getvalue()
        self.assertIn("Windows:", output)
        self.assertIn("Chrome", output)
        self.assertIn("Firefox", output)

if __name__ == '__main__':
    unittest.main()
