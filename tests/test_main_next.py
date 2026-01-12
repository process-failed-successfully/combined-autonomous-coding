
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import shutil
from pathlib import Path
import asyncio
from argparse import Namespace

from main import run_next, parse_args

class TestMainNextCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_main_next_")
        self.project_dir = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    @patch('main.get_suggestions', return_value=[])
    async def test_run_next_no_suggestions(self, mock_get_suggestions):
        args = Namespace(project_dir=self.project_dir, yes=False)
        with self.assertRaises(SystemExit) as cm:
            await run_next(args)
        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)

    @patch('main.run_status')
    @patch('builtins.input', return_value='y')
    @patch('main.get_suggestions', return_value=[{'command': './main.py status', 'reason': 'Check status'}])
    async def test_run_next_with_suggestion_and_confirmation(self, mock_get_suggestions, mock_input, mock_run_status):
        args = Namespace(project_dir=self.project_dir, yes=False)
        mock_run_status.side_effect = SystemExit(0)

        with self.assertRaises(SystemExit) as cm:
            await run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_run_status.assert_called_once()

    @patch('main.run_status')
    @patch('builtins.input', return_value='n')
    @patch('main.get_suggestions', return_value=[{'command': './main.py status', 'reason': 'Check status'}])
    async def test_run_next_with_suggestion_and_rejection(self, mock_get_suggestions, mock_input, mock_run_status):
        args = Namespace(project_dir=self.project_dir, yes=False)
        with self.assertRaises(SystemExit) as cm:
            await run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_run_status.assert_not_called()

    @patch('main.run_status')
    @patch('builtins.input')
    @patch('main.get_suggestions', return_value=[{'command': './main.py status', 'reason': 'Check status'}])
    async def test_run_next_with_yes_flag(self, mock_get_suggestions, mock_input, mock_run_status):
        args = Namespace(project_dir=self.project_dir, yes=True)
        mock_run_status.side_effect = SystemExit(0)
        with self.assertRaises(SystemExit) as cm:
            await run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_not_called()
        mock_run_status.assert_called_once()

    @patch('main.run_plan', new_callable=AsyncMock)
    @patch('builtins.input', return_value='y')
    @patch('main.get_suggestions', return_value=[{'command': './main.py plan --spec app_spec.txt', 'reason': 'Generate plan'}])
    async def test_run_next_with_async_command(self, mock_get_suggestions, mock_input, mock_run_plan):
        args = Namespace(project_dir=self.project_dir, yes=False)
        mock_run_plan.side_effect = SystemExit(0)

        # We need to mock parse_args to return the correct namespace for the subcommand
        def side_effect(argv):
            if argv == ['plan', '--spec', 'app_spec.txt']:
                return Namespace(command='plan', spec='app_spec.txt')
            return parse_args(argv)

        with patch('main.parse_args', side_effect=side_effect):
            with self.assertRaises(SystemExit) as cm:
                await run_next(args)

        self.assertEqual(cm.exception.code, 0)
        mock_get_suggestions.assert_called_once_with(project_dir=self.project_dir, limit=1)
        mock_input.assert_called_once()
        mock_run_plan.assert_called_once()

if __name__ == '__main__':
    unittest.main()
