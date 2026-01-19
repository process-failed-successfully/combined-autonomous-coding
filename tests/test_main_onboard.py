import unittest
from unittest.mock import patch, MagicMock
import argparse
# Need to import run_onboard from main.
# Since main.py has code that runs on import (if __name__ == "__main__"), but it's guarded.
from main import run_onboard


class TestMainOnboard(unittest.TestCase):
    @patch("main.run_onboard_logic")
    @patch("main.sys.exit")
    def test_run_onboard_calls_logic(self, mock_exit, mock_logic):
        args = argparse.Namespace(project_dir=MagicMock())

        run_onboard(args)

        mock_logic.assert_called_once_with(args.project_dir)
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
