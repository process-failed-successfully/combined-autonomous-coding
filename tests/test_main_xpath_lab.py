from main import run_xpath_lab
from unittest.mock import patch, MagicMock
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@patch('main.run_xpath_lab_logic')
def test_run_xpath_lab_evaluate(mock_run):
    args = argparse.Namespace(action='evaluate')
    with patch('sys.exit'):
        run_xpath_lab(args)
    mock_run.assert_called_once_with(args)


@patch('shared.tui.AgentTUI')
def test_run_xpath_lab_tui(mock_run):
    args = argparse.Namespace(action='tui', project_dir=None)
    with patch('sys.exit'):
        run_xpath_lab(args)
    mock_run.return_value.run.assert_called_once()


@patch('shared.tui.AgentTUI')
def test_run_xpath_lab_tui_async(mock_run_async):
    args = argparse.Namespace(action='tui', project_dir=None)

    # We mock asyncio.get_running_loop to return a mock loop that is running
    mock_loop = MagicMock()
    mock_loop.is_running.return_value = True

    with patch('sys.exit'):
        with patch('asyncio.get_running_loop', return_value=mock_loop):
            with patch('asyncio.ensure_future') as mock_ensure:
                run_xpath_lab(args)
                mock_ensure.assert_called_once()


@patch('sys.stderr', new_callable=MagicMock)
def test_run_xpath_lab_invalid(mock_stderr):
    args = argparse.Namespace(action='invalid')
    with patch('sys.exit'):
        run_xpath_lab(args)
