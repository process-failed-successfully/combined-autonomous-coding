import argparse
import io
import sys
import unittest
from unittest.mock import patch, MagicMock
from shared.base85_lab import run_base85_lab_logic
from main import run_base85_lab
import base64

class TestBase85Lab(unittest.TestCase):
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
        result = run_base85_lab_logic(args)
        self.assertTrue(result)
        # b85encode('hello world') = 'Xk~0{Zy<MXa%^M' (python base64.b85encode uses standard base85 by default)
        self.assertEqual(self.held_stdout.getvalue().strip(), "Xk~0{Zy<MXa%^M")

    def test_decode(self):
        args = argparse.Namespace(encode=None, decode="Xk~0{Zy<MXa%^M", tui=False)
        result = run_base85_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(self.held_stdout.getvalue().strip(), "hello world")

    def test_no_args(self):
        args = argparse.Namespace(encode=None, decode=None, tui=False)
        result = run_base85_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error: must provide either --encode, --decode, or --tui", self.held_stderr.getvalue())

    def test_invalid_decode(self):
        args = argparse.Namespace(encode=None, decode="INVALID BASE85!!!", tui=False)
        result = run_base85_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error processing base85:", self.held_stderr.getvalue())

    @patch('main.sys.exit')
    @patch('shared.tui.AgentTUI')
    def test_run_base85_lab_tui(self, mock_agent_tui, mock_exit):
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        # Mock sys.exit to raise an exception so we don't fall through to the logic block
        mock_exit.side_effect = SystemExit
        args = argparse.Namespace(command="base85-lab", tui=True, project_dir=None)

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_base85_lab(args)
            except SystemExit:
                pass

        mock_agent_tui.assert_called_once_with(project_dir=None, start_tab="tab-base85")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_once_with(0)

    @patch('main.sys.exit')
    @patch('shared.base85_lab.run_base85_lab_logic')
    def test_run_base85_lab_cli(self, mock_logic, mock_exit):
        mock_logic.return_value = True
        args = argparse.Namespace(command="base85", tui=False, encode="test")

        with patch.dict('sys.modules', {'shared.base85_lab': MagicMock(run_base85_lab_logic=mock_logic)}):
            run_base85_lab(args)

        mock_logic.assert_called_once_with(args)
        mock_exit.assert_called_once_with(0)

if __name__ == '__main__':
    unittest.main()
