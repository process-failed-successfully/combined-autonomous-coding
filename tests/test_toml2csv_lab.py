import unittest
import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.toml2csv_lab import Toml2CsvManager, run_toml2csv_lab_logic

class TestToml2CsvLab(unittest.TestCase):
    def setUp(self):
        self.manager = Toml2CsvManager()

    def test_convert_raw_string(self):
        toml_data = """
[[items]]
name = "Alice"
age = 30
city = "New York"

[[items]]
name = "Bob"
age = 25
city = "London"
"""
        expected = "age,city,name\r\n30,New York,Alice\r\n25,London,Bob\r\n"
        result = self.manager.convert(toml_data)
        self.assertEqual(result, expected)

    def test_convert_with_custom_delimiter(self):
        toml_data = """
[[items]]
name = "Alice"
age = 30
city = "New York"

[[items]]
name = "Bob"
age = 25
city = "London"
"""
        expected = "age;city;name\r\n30;New York;Alice\r\n25;London;Bob\r\n"
        result = self.manager.convert(toml_data, delimiter=";")
        self.assertEqual(result, expected)

    def test_convert_single_table(self):
        toml_data = """
[user]
name = "Charlie"
age = 40
"""
        expected = "user.age,user.name\r\n40,Charlie\r\n"
        result = self.manager.convert(toml_data)
        self.assertEqual(result, expected)

    def test_convert_nested_array(self):
        toml_data = """
[[items]]
name = "Dave"
tags = ["admin", "staff"]
"""
        # tags array will be converted to json string
        expected = 'name,tags\r\nDave,"[""admin"", ""staff""]"\r\n'
        result = self.manager.convert(toml_data)
        self.assertEqual(result, expected)

    @patch('builtins.print')
    def test_cli_logic_text(self, mock_print):
        args = argparse.Namespace(
            text="[[items]]\nname='Eve'",
            file=None,
            output=None,
            delimiter=",",
            action=None,
            tui=False
        )
        run_toml2csv_lab_logic(args)
        mock_print.assert_called()

    @patch('sys.stderr.write')
    @patch('sys.stdin.isatty', return_value=True)
    def test_cli_logic_missing_args(self, mock_isatty, mock_stderr):
        args = argparse.Namespace(text=None, file=None, action=None, tui=False)
        with self.assertRaises(SystemExit) as cm:
            run_toml2csv_lab_logic(args)
        self.assertEqual(cm.exception.code, 1)
        mock_stderr.assert_called()

    def test_cli_logic_tui(self):
        args = argparse.Namespace(tui=True, action=None)

        mock_app = MagicMock()
        mock_agent_tui = MagicMock(return_value=mock_app)

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            with patch('asyncio.get_running_loop') as mock_get_running_loop:
                mock_get_running_loop.side_effect = RuntimeError("no loop")
                with self.assertRaises(SystemExit) as cm:
                    run_toml2csv_lab_logic(args)
                self.assertEqual(cm.exception.code, 0)

                mock_app.run.assert_called_once()

if __name__ == "__main__":
    unittest.main()
