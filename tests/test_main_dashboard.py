
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import contextlib
from pathlib import Path

import main


class TestMainDashboard(unittest.TestCase):
    @patch('main._run_dashboard_logic')
    def test_run_dashboard(self, mock_dashboard_logic):
        # Arrange
        mock_dashboard_logic.return_value = "Mocked Dashboard Output"

        args = MagicMock()
        args.project_dir = Path("/tmp/project")

        output_buffer = StringIO()

        # Act & Assert
        with self.assertRaises(SystemExit) as cm, contextlib.redirect_stdout(output_buffer):
            main.run_dashboard(args)

        self.assertEqual(cm.exception.code, 0)

        # Assert that the logic function was called correctly
        mock_dashboard_logic.assert_called_once_with(project_dir=args.project_dir)

        # Assert that the output was printed to the console
        self.assertIn("Mocked Dashboard Output", output_buffer.getvalue())


if __name__ == '__main__':
    unittest.main()
