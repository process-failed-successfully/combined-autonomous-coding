import pytest
import sys
from tests.test_stego_lab import DummyArgs, temp_image, temp_output
from shared.stego_lab import StegoManager, run_stego_lab_logic
import os

from unittest.mock import patch

@patch('sys.exit')
@patch('builtins.print')
def test_run_stego_lab_logic_hide(mock_print, mock_exit, temp_image, temp_output):
    args = DummyArgs(action="hide", image=temp_image, message="Secret", output=temp_output)
    print(f"args: {args.image}, {args.message}, {args.output}")
    run_stego_lab_logic(args)
    print(f"mock exit calls: {mock_exit.call_args_list}")
