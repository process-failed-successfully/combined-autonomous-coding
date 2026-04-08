import unittest
import io
import sys
from unittest.mock import patch, MagicMock
from argparse import Namespace
from shared.csv2xml_lab import Csv2XmlManager, run_csv2xml_lab_logic

class TestCsv2XmlLab(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2XmlManager()

    def test_convert_basic(self):
        csv_data = "id,name,age\n1,Alice,30\n2,Bob,25"
        xml_output = self.manager.convert(csv_data)
        self.assertIn("<root>", xml_output)
        self.assertIn("</root>", xml_output)
        self.assertIn("<item>", xml_output)
        self.assertIn("<id>1</id>", xml_output)
        self.assertIn("<name>Alice</name>", xml_output)
        self.assertIn("<age>30</age>", xml_output)
        self.assertIn("<id>2</id>", xml_output)
        self.assertIn("<name>Bob</name>", xml_output)
        self.assertIn("<age>25</age>", xml_output)

    def test_convert_custom_names(self):
        csv_data = "col1,col2\nval1,val2"
        xml_output = self.manager.convert(csv_data, root_name="dataset", item_name="record")
        self.assertIn("<dataset>", xml_output)
        self.assertIn("<record>", xml_output)
        self.assertIn("<col1>val1</col1>", xml_output)
        self.assertIn("<col2>val2</col2>", xml_output)

    def test_convert_invalid_headers(self):
        csv_data = "123 invalid,valid_header, header space \nval1,val2,val3"
        xml_output = self.manager.convert(csv_data)
        # Should sanitize '123 invalid' -> col_123invalid, ' header space ' -> headerspace
        self.assertIn("<col_123invalid>val1</col_123invalid>", xml_output)
        self.assertIn("<valid_header>val2</valid_header>", xml_output)
        self.assertIn("<headerspace>val3</headerspace>", xml_output)

    def test_convert_empty(self):
        self.assertEqual(self.manager.convert(""), "")
        self.assertEqual(self.manager.convert("   \n"), "")

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_run_csv2xml_lab_logic_text(self, mock_stdout):
        args = Namespace(text="a,b\n1,2", file=None, delimiter=",", root="root", item="item", output=None)
        success = run_csv2xml_lab_logic(args)
        self.assertTrue(success)
        output = mock_stdout.getvalue()
        self.assertIn("<root>", output)
        self.assertIn("<a>1</a>", output)
        self.assertIn("<b>2</b>", output)

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    @patch('sys.stdin.isatty', return_value=True)
    def test_run_csv2xml_lab_logic_no_input(self, mock_isatty, mock_exit, mock_stderr):
        args = Namespace(text=None, file=None, delimiter=",", root="root", item="item", output=None)
        run_csv2xml_lab_logic(args)
        mock_exit.assert_called_once_with(1)
        self.assertIn("Error: Input required", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main()
