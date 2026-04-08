import unittest
from unittest.mock import MagicMock, patch
import sys
import io

from shared.slug_lab import SlugManager, run_slug_lab_logic

class TestSlugManager(unittest.TestCase):
    def setUp(self):
        self.manager = SlugManager()

    def test_generate_slug_basic(self):
        self.assertEqual(self.manager.generate_slug("Hello World"), "hello-world")
        self.assertEqual(self.manager.generate_slug("Test 123"), "test-123")

    def test_generate_slug_empty(self):
        self.assertEqual(self.manager.generate_slug(""), "")
        self.assertEqual(self.manager.generate_slug(None), "")

    def test_generate_slug_special_chars(self):
        self.assertEqual(self.manager.generate_slug("Hello @ World! #123"), "hello-world-123")
        self.assertEqual(self.manager.generate_slug("   trailing spaces   "), "trailing-spaces")
        self.assertEqual(self.manager.generate_slug("---multiple---hyphens---"), "multiple-hyphens")

    def test_generate_slug_unicode(self):
        self.assertEqual(self.manager.generate_slug("Âñtëññà"), "antenna")
        self.assertEqual(self.manager.generate_slug("Café & Résumé"), "cafe-resume")
        self.assertEqual(self.manager.generate_slug("München"), "munchen")


class TestSlugLabCLI(unittest.TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_run_slug_lab_logic_text_arg(self, mock_exit, mock_stdout):
        args = MagicMock()
        args.text = "Hello World!"
        args.tui = False

        run_slug_lab_logic(args)

        self.assertEqual(mock_stdout.getvalue().strip(), "hello-world")
        mock_exit.assert_called_once_with(0)

    @patch('sys.stdin.isatty', return_value=False)
    @patch('sys.stdin.read', return_value="From Stdin!")
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_run_slug_lab_logic_stdin(self, mock_exit, mock_stdout, mock_stdin_read, mock_isatty):
        args = MagicMock()
        args.text = None
        args.tui = False

        run_slug_lab_logic(args)

        self.assertEqual(mock_stdout.getvalue().strip(), "from-stdin")
        mock_exit.assert_called_once_with(0)

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_run_slug_lab_logic_no_input(self, mock_exit, mock_stderr):
        args = MagicMock()
        args.text = None
        args.tui = False
        mock_exit.side_effect = SystemExit

        with patch('sys.stdin.isatty', return_value=True):
            with self.assertRaises(SystemExit):
                run_slug_lab_logic(args)

            self.assertIn("Error: Input text required", mock_stderr.getvalue())
            mock_exit.assert_called_once_with(1)

    @patch('main.run_tui')
    @patch('asyncio.get_running_loop', side_effect=RuntimeError('no loop'))
    def test_run_slug_lab_logic_tui(self, mock_loop, mock_run_tui):
        args = MagicMock()
        args.tui = True

        run_slug_lab_logic(args)

        mock_run_tui.assert_called_once_with(args, start_tab="tab-slug")


if __name__ == '__main__':
    unittest.main()
