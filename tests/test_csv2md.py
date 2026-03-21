import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from io import StringIO
from shared.csv2md_lab import Csv2MdManager, run_csv2md_lab_logic


class TestCsv2MdManager(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2MdManager()

    def test_convert_valid_csv(self):
        csv_content = "Name,Age,City\nAlice,30,New York\nBob,25,Los Angeles"
        expected_md = "| Name | Age | City |\n|---|---|---|\n| Alice | 30 | New York |\n| Bob | 25 | Los Angeles |"
        result = self.manager.convert(csv_content)
        self.assertEqual(result, expected_md)

    def test_convert_empty_csv(self):
        csv_content = ""
        expected_md = ""
        result = self.manager.convert(csv_content)
        self.assertEqual(result, expected_md)

    def test_convert_custom_delimiter(self):
        csv_content = "Name;Age;City\nAlice;30;New York"
        expected_md = "| Name | Age | City |\n|---|---|---|\n| Alice | 30 | New York |"
        result = self.manager.convert(csv_content, delimiter=";")
        self.assertEqual(result, expected_md)

    def test_convert_uneven_rows(self):
        csv_content = "Col1,Col2\nA,B\nC,D,E\nF"
        expected_md = "| Col1 | Col2 |\n|---|---|\n| A | B |\n| C | D |\n| F |  |"
        result = self.manager.convert(csv_content)
        self.assertEqual(result, expected_md)

    @patch('shared.csv2md_lab.Path.exists', return_value=True)
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Name,Age\nAlice,30")
    def test_process_file_stdout(self, mock_open, mock_exists):
        filepath = Path("dummy.csv")
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = self.manager.process_file(filepath)
            self.assertTrue(result)
            self.assertIn("| Name | Age |", fake_out.getvalue())

    @patch('shared.csv2md_lab.Path.exists', return_value=False)
    def test_process_file_not_found(self, mock_exists):
        filepath = Path("dummy.csv")
        with patch('sys.stderr', new=StringIO()) as fake_err:
            result = self.manager.process_file(filepath)
            self.assertFalse(result)
            self.assertIn("not found", fake_err.getvalue())


class TestCsv2MdLabLogic(unittest.TestCase):
    @patch('shared.csv2md_lab.Csv2MdManager.process_file', return_value=True)
    def test_logic_with_file(self, mock_process):
        args = MagicMock()
        args.file = "dummy.csv"
        args.output = "output.md"
        args.delimiter = ","
        args.text = None
        result = run_csv2md_lab_logic(args)
        self.assertTrue(result)
        mock_process.assert_called_once()

    @patch('shared.csv2md_lab.Csv2MdManager.convert', return_value="| a |")
    def test_logic_with_text(self, mock_convert):
        args = MagicMock()
        args.file = None
        args.output = None
        args.text = "a\n1"
        args.delimiter = ","
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = run_csv2md_lab_logic(args)
            self.assertTrue(result)
            self.assertIn("| a |", fake_out.getvalue())
        mock_convert.assert_called_once()

    def test_logic_no_input(self):
        args = MagicMock()
        args.file = None
        args.text = None
        with patch('sys.stderr', new=StringIO()) as fake_err:
            result = run_csv2md_lab_logic(args)
            self.assertFalse(result)
            self.assertIn("must be provided", fake_err.getvalue())


if __name__ == '__main__':
    unittest.main()
