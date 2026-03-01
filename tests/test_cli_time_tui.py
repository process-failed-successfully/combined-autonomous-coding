import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

import main


class TestCliTimeTui(unittest.TestCase):
    @patch('sys.exit')
    @patch('shared.tui.AgentTUI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_time_lab_tui_command(self, mock_stdout, mock_agent_tui, mock_exit):
        """Test that 'main.py time-lab tui' correctly mounts and runs the Time Lab TUI."""
        mock_app_instance = MagicMock()
        mock_agent_tui.return_value = mock_app_instance

        args = ["time-lab", "tui"]
        try:
            main.parse_args(args)
        except SystemExit:
            pass  # argparse throws SystemExit on help, but here we just want to ensure parsing works

        args_obj = main.parse_args(args)
        main.run_time_lab(args_obj)

        # Assert AgentTUI was called with right args
        mock_agent_tui.assert_called_once_with(project_dir=args_obj.project_dir, start_tab="tab-time")

        # Assert app.run() was called
        mock_app_instance.run.assert_called_once()

        # Assert proper output
        self.assertIn("Launching Time Lab TUI...", mock_stdout.getvalue())

        # Assert sys.exit(0) was called
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
