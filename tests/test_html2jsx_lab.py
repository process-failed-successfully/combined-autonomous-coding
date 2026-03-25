import unittest
import argparse
from io import StringIO
from unittest.mock import patch

from shared.html2jsx_lab import Html2JsxManager, run_html2jsx_lab_logic


class TestHtml2JsxLab(unittest.TestCase):
    def setUp(self):
        self.manager = Html2JsxManager()

    def test_class_and_for_attributes(self):
        html = '<div class="container"><label for="username">Name</label></div>'
        expected = '<div className="container"><label htmlFor="username">Name</label></div>'
        self.assertEqual(self.manager.convert(html), expected)

    def test_self_closing_tags(self):
        html = '<div><img src="test.png"><br><input type="text"></div>'
        expected = '<div><img src="test.png" /><br /><input type="text" /></div>'
        self.assertEqual(self.manager.convert(html), expected)

    def test_inline_style(self):
        html = '<div style="color: red; margin-top: 10px; font-size: 14px;">Test</div>'
        expected = "<div style={{color: 'red', marginTop: '10px', fontSize: '14px'}}>Test</div>"
        self.assertEqual(self.manager.convert(html), expected)

    def test_camel_case_attributes(self):
        html = '<svg stroke-width="2" fill-rule="evenodd" data-test="keep-dash" aria-label="keep-dash"></svg>'
        expected = '<svg strokeWidth="2" fillRule="evenodd" data-test="keep-dash" aria-label="keep-dash"></svg>'
        self.assertEqual(self.manager.convert(html), expected)

    def test_boolean_attributes(self):
        html = '<input type="checkbox" checked disabled readonly>'
        expected = '<input type="checkbox" checked disabled readOnly />'
        self.assertEqual(self.manager.convert(html), expected)

    def test_text_escaping(self):
        html = '<div>{test} & "quotes"</div>'
        expected = '<div>&#123;test&#125; & "quotes"</div>'
        self.assertEqual(self.manager.convert(html), expected)

    def test_script_style_escaping(self):
        html = '<style>.test { color: red; }</style><script>function t() { return 1; }</script>'
        expected = '<style>.test { color: red; }</style><script>function t() { return 1; }</script>'
        self.assertEqual(self.manager.convert(html), expected)

    def test_create_component(self):
        html = '<div class="test">Hello</div>'
        expected = "export default function TestComp() {\n  return (\n    <>\n      <div className=\"test\">Hello</div>\n    </>\n  );\n}"
        self.assertEqual(self.manager.convert(html, create_component=True, component_name="TestComp"), expected)

    def test_empty_input(self):
        self.assertEqual(self.manager.convert(""), "")
        self.assertEqual(self.manager.convert("   "), "")

    @patch('sys.stdout', new_callable=StringIO)
    def test_run_logic_text(self, mock_stdout):
        args = argparse.Namespace(text='<div class="x"></div>', file=None, output=None, component=False, name="MyComponent")
        result = run_html2jsx_lab_logic(args)
        self.assertTrue(result)
        self.assertEqual(mock_stdout.getvalue().strip(), '<div className="x"></div>')

    @patch('sys.stdout', new_callable=StringIO)
    @patch('pathlib.Path.write_text')
    def test_run_logic_output_file(self, mock_write, mock_stdout):
        args = argparse.Namespace(text='<br>', file=None, output='out.jsx', component=False, name="MyComponent")
        result = run_html2jsx_lab_logic(args)
        self.assertTrue(result)
        mock_write.assert_called_once_with('<br />', encoding='utf-8')
        self.assertIn("Saved JSX to out.jsx", mock_stdout.getvalue())

    @patch('sys.stderr', new_callable=StringIO)
    def test_run_logic_no_input(self, mock_stderr):
        args = argparse.Namespace(text=None, file=None, output=None, component=False, name="MyComponent")
        with patch('sys.stdin.isatty', return_value=True):
            result = run_html2jsx_lab_logic(args)
            self.assertFalse(result)
            self.assertIn("Input required", mock_stderr.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.stdin.read', return_value='<hr>')
    def test_run_logic_stdin(self, mock_stdin_read, mock_stdout):
        args = argparse.Namespace(text=None, file=None, output=None, component=False, name="MyComponent")
        with patch('sys.stdin.isatty', return_value=False):
            result = run_html2jsx_lab_logic(args)
            self.assertTrue(result)
            self.assertEqual(mock_stdout.getvalue().strip(), '<hr />')


if __name__ == '__main__':
    unittest.main()
