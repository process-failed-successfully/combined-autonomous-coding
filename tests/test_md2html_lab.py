import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
from io import StringIO
from shared.md2html_lab import Md2HtmlManager, run_md2html_logic

class TestMd2HtmlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Md2HtmlManager()

    def test_convert_basic_markdown(self):
        md = "# Hello\n\nThis is **bold** text."
        expected_html = "<h1>Hello</h1>\n<p>This is <strong>bold</strong> text.</p>\n"
        result = self.manager.convert(md)
        self.assertEqual(result, expected_html)

    def test_convert_list(self):
        md = "- Item 1\n- Item 2"
        expected_html = "<ul>\n<li>Item 1</li>\n<li>Item 2</li>\n</ul>\n"
        result = self.manager.convert(md)
        self.assertEqual(result, expected_html)

class TestMd2HtmlCLI(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_with_text(self, mock_stdout):
        args = MagicMock()
        args.file = None
        args.text = "# Title"
        args.output = None

        success = run_md2html_logic(args)
        self.assertTrue(success)
        self.assertIn("<h1>Title</h1>", mock_stdout.getvalue())

    @patch('shared.md2html_lab.Path')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_with_file(self, mock_stdout, mock_path):
        args = MagicMock()
        args.file = "input.md"
        args.text = None
        args.output = None

        mock_instance = MagicMock()
        mock_instance.read_text.return_value = "## Subtitle"
        mock_path.return_value = mock_instance

        success = run_md2html_logic(args)
        self.assertTrue(success)
        self.assertIn("<h2>Subtitle</h2>", mock_stdout.getvalue())

    @patch('shared.md2html_lab.Path')
    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_with_output_file(self, mock_stdout, mock_path):
        args = MagicMock()
        args.file = None
        args.text = "Just text"
        args.output = "output.html"

        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        success = run_md2html_logic(args)
        self.assertTrue(success)
        mock_instance.write_text.assert_called_once_with("<p>Just text</p>\n", encoding="utf-8")
        self.assertIn("✅ HTML saved to output.html", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
