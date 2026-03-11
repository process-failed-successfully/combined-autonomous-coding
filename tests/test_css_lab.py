import unittest
import argparse
from io import StringIO
from unittest.mock import patch
from shared.css_lab import CssLabManager, run_css_lab_logic

class TestCssLab(unittest.TestCase):
    def setUp(self):
        self.manager = CssLabManager()

    def test_minify(self):
        input_css = """
        /* This is a comment */
        body {
            background-color: #fff;
            content: " : ";
            width: calc(100% - 10px);
            color: #333;
        }

        h1 {
            font-size: 2em;
        }
        """
        expected_output = 'body{background-color:#fff;content:" : ";width:calc(100% - 10px);color:#333}h1{font-size:2em}'
        self.assertEqual(self.manager.minify(input_css), expected_output)

    def test_format(self):
        input_css = 'body{background-color:#fff;content:" : ";width:calc(100% - 10px);color:#333}h1{font-size:2em}'
        expected_output = 'body {\n    background-color:#fff;\n    content:" : ";\n    width:calc(100% - 10px);\n    color:#333;\n}\n\nh1 {\n    font-size:2em;\n}'
        self.assertEqual(self.manager.format(input_css), expected_output)

    @patch('builtins.print')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="body { color: red; }")
    def test_run_logic_minify(self, mock_open, mock_print):
        args = argparse.Namespace(action="minify", file="test.css", output=None)
        self.assertTrue(run_css_lab_logic(args))
        mock_print.assert_called_with("body{color:red}")

    @patch('builtins.print')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="body{color:red}")
    def test_run_logic_format(self, mock_open, mock_print):
        args = argparse.Namespace(action="format", file="test.css", output=None)
        self.assertTrue(run_css_lab_logic(args))
        mock_print.assert_called_with("body {\n    color:red;\n}")

if __name__ == '__main__':
    unittest.main()
