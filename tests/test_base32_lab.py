import argparse
import io
import sys
import unittest
from unittest.mock import patch, MagicMock
from shared.base32_lab import run_base32_lab_logic
from main import run_base32_lab
import base64

class TestBase32Lab(unittest.TestCase):
    def setUp(self):
        self.held_stdout = io.StringIO()
        self.held_stderr = io.StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    def tearDown(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def test_encode(self):
        args = argparse.Namespace(encode="hello world", decode=None, tui=False)
        result = run_base32_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "NBSWY3DPEB3W64TMMQ======")

    def test_decode(self):
        args = argparse.Namespace(encode=None, decode="NBSWY3DPEB3W64TMMQ======", tui=False)
        result = run_base32_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "hello world")

    def test_no_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_base32_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", self.held_stderr.getvalue())

    def test_invalid_decode(self):
        args = argparse.Namespace(encode=None, decode="INVALIDBASE32!!!", tui=False)
        result = run_base32_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error processing base32:", self.held_stderr.getvalue())

    @patch('main.sys.exit')
    @patch('shared.tui.AgentTUI')
    def test_run_base32_lab_tui(self, mock_agent_tui, mock_exit):
        # We need to test the local import patch
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        args = argparse.Namespace(command="base32-lab", tui=True, project_dir=None)

        # Test requires importing the local AgentTUI within run_base32_lab
        # We'll just patch the sys.modules to return our mock
        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            run_base32_lab(args)

        mock_agent_tui.assert_called_once_with(project_dir=None, start_tab="tab-base32")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.sys.exit')
    @patch('shared.base32_lab.run_base32_lab_logic')
    def test_run_base32_lab_cli(self, mock_logic, mock_exit):
        mock_logic.return_value = True
        args = argparse.Namespace(command="base32", tui=False, encode="test")

        with patch.dict('sys.modules', {'shared.base32_lab': MagicMock(run_base32_lab_logic=mock_logic)}):
            run_base32_lab(args)

        mock_logic.assert_called_once_with(args)
        mock_exit.assert_called_once_with(0)

if __name__ == '__main__':
    unittest.main()
