import unittest
import json
import argparse
from unittest.mock import patch, MagicMock


from shared.ini2json_lab import Ini2JsonManager, run_ini2json_lab_logic


class TestIni2JsonManager(unittest.TestCase):
    def setUp(self):
        self.manager = Ini2JsonManager()

    def test_empty_ini(self):
        result = self.manager.convert("")
        self.assertEqual(result, "{}")

    def test_simple_ini_conversion(self):
        ini_data = """
        [server]
        port = 8080
        host = 127.0.0.1
        enabled = true

        [database]
        name = mydb
        timeout = 30.5
        """

        json_output = self.manager.convert(ini_data)
        parsed = json.loads(json_output)

        self.assertIn("server", parsed)
        self.assertEqual(parsed["server"]["port"], 8080)
        self.assertEqual(parsed["server"]["host"], "127.0.0.1")
        self.assertEqual(parsed["server"]["enabled"], True)

        self.assertIn("database", parsed)
        self.assertEqual(parsed["database"]["name"], "mydb")
        self.assertEqual(parsed["database"]["timeout"], 30.5)

    def test_defaults_section(self):
        ini_data = """
        [DEFAULT]
        env = production
        debug = false

        [app]
        name = my_app
        """

        json_output = self.manager.convert(ini_data)
        parsed = json.loads(json_output)

        self.assertIn("DEFAULT", parsed)
        self.assertEqual(parsed["DEFAULT"]["env"], "production")
        self.assertEqual(parsed["DEFAULT"]["debug"], False)

        self.assertIn("app", parsed)
        self.assertEqual(parsed["app"]["name"], "my_app")
        # Ensure DEFAULT values propagate as configparser does
        self.assertEqual(parsed["app"]["env"], "production")
        self.assertEqual(parsed["app"]["debug"], False)

    def test_invalid_ini(self):
        ini_data = """
        this is not an ini string
        foo bar
        """
        with self.assertRaises(ValueError):
            self.manager.convert(ini_data)


class TestIni2JsonCLI(unittest.TestCase):

    @patch('sys.stdout', new_callable=MagicMock)
    @patch('sys.stderr', new_callable=MagicMock)
    @patch('sys.exit')
    def test_cli_missing_input(self, mock_exit, mock_stderr, mock_stdout):
        args = argparse.Namespace(file=None, text=None, output=None, tui=False, action=None)

        with patch('sys.stdin.isatty', return_value=True):
            run_ini2json_lab_logic(args)

        mock_exit.assert_called_with(1)

    @patch('builtins.print')
    @patch('sys.exit')
    def test_cli_valid_text_input(self, mock_exit, mock_print):
        ini_text = "[foo]\nbar=baz"
        args = argparse.Namespace(text=ini_text, file=None, output=None, tui=False, action=None)

        run_ini2json_lab_logic(args)

        # Verify that json containing 'foo' and 'bar' was printed
        printed_output = mock_print.call_args[0][0]
        self.assertIn('"foo"', printed_output)
        self.assertIn('"bar"', printed_output)
        self.assertIn('"baz"', printed_output)
        mock_exit.assert_not_called()  # Assuming success doesn't sys.exit unless TUI


if __name__ == '__main__':
    unittest.main()
