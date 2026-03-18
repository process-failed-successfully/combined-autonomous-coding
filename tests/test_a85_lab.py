import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import io

from shared.a85_lab import run_a85_lab_logic
from main import run_a85_lab


class TestA85Lab(unittest.TestCase):
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

    def test_run_a85_lab_logic_encode(self):
        args = argparse.Namespace(encode="hello world", decode=None)
        result = run_a85_lab_logic(args)
        self.assertTrue(result)
        # base64.a85encode(b'hello world') = b'BOu!rD]j7BEbo7'
        self.assertIn("BOu!rD]j7BEbo7", self.held_stdout.getvalue())

    def test_run_a85_lab_logic_decode(self):
        args = argparse.Namespace(encode=None, decode="BOu!rD]j7BEbo7")
        result = run_a85_lab_logic(args)
        self.assertTrue(result)
        self.assertIn("hello world", self.held_stdout.getvalue())

    def test_run_a85_lab_logic_no_args(self):
        args = argparse.Namespace(encode=None, decode=None)
        result = run_a85_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("must provide either --encode, --decode, or --tui", self.held_stderr.getvalue())

    def test_run_a85_lab_logic_exception(self):
        # Invalid ascii85 decode sequence (not long enough, bad chars, etc)
        args = argparse.Namespace(encode=None, decode="!!!bad data")
        result = run_a85_lab_logic(args)
        self.assertFalse(result)
        self.assertIn("Error processing a85:", self.held_stderr.getvalue())

    @patch('shared.tui.AgentTUI')
    @patch('sys.exit')
    def test_run_a85_lab_tui(self, mock_exit, mock_agent_tui):
        mock_exit.side_effect = SystemExit

        mock_app_instance = MagicMock()
        mock_agent_tui.return_value = mock_app_instance

        args = argparse.Namespace(command="a85-lab", tui=True, project_dir=None)

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_a85_lab(args)
            except SystemExit:
                pass

        mock_agent_tui.assert_called_once_with(project_dir=None, start_tab="tab-a85")
        mock_app_instance.run.assert_called_once()

    @patch('shared.a85_lab.run_a85_lab_logic')
    @patch('sys.exit')
    def test_run_a85_lab_cli(self, mock_exit, mock_logic):
        mock_logic.return_value = True
        args = argparse.Namespace(command="a85", tui=False, encode="test")

        with patch.dict('sys.modules', {'shared.a85_lab': MagicMock(run_a85_lab_logic=mock_logic)}):
            run_a85_lab(args)

        mock_logic.assert_called_once_with(args)
        mock_exit.assert_called_once_with(0)
