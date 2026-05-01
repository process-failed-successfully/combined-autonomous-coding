import unittest
import argparse
from unittest.mock import patch, MagicMock
from shared.json2ini_lab import Json2IniManager, run_json2ini_lab_logic


class TestJson2IniLab(unittest.TestCase):
    def setUp(self):
        self.manager = Json2IniManager()

    def test_simple_conversion(self):
        json_data = '{"key1": "value1", "key2": 123}'
        ini_str = self.manager.convert(json_data)

        # It should place top-level primitives in [Global]
        self.assertIn("[Global]", ini_str)
        self.assertIn("key1 = value1", ini_str)
        self.assertIn("key2 = 123", ini_str)

    def test_nested_conversion(self):
        json_data = '{"database": {"host": "localhost", "port": 5432}, "user": "admin"}'
        ini_str = self.manager.convert(json_data)

        # Sections should be created
        self.assertIn("[database]", ini_str)
        self.assertIn("host = localhost", ini_str)
        self.assertIn("port = 5432", ini_str)

        # Top-level primitives go to Global
        self.assertIn("[Global]", ini_str)
        self.assertIn("user = admin", ini_str)

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            self.manager.convert('{"bad_json": }')

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            # INI expects a dict
            self.manager.convert('[1, 2, 3]')

    def test_boolean_and_null(self):
        json_data = '{"is_active": true, "deleted": false, "name": null}'
        ini_str = self.manager.convert(json_data)

        self.assertIn("is_active = true", ini_str)
        self.assertIn("deleted = false", ini_str)
        self.assertIn("name = ", ini_str)

    def test_nested_lists_and_dicts(self):
        json_data = '{"complex": {"list": [1, 2, 3], "dict": {"a": "b"}}}'
        ini_str = self.manager.convert(json_data)

        self.assertIn("[complex]", ini_str)
        self.assertIn("list = [1, 2, 3]", ini_str)
        self.assertIn('dict = {"a": "b"}', ini_str)

    @patch('builtins.print')
    def test_cli_logic_text(self, mock_print):
        args = argparse.Namespace(text='{"a": "b"}', file=None, output=None, tui=False)
        # Assuming run_json2ini_lab_logic finishes successfully and prints
        run_json2ini_lab_logic(args)
        # The print may be called with multiple arguments or end=""
        mock_print.assert_called()

    @patch('sys.stderr.write')
    @patch('sys.exit')
    def test_cli_logic_missing_input(self, mock_exit, mock_stderr):
        # By mocking isatty to return True, we skip reading from stdin
        with patch('sys.stdin.isatty', return_value=True):
            args = argparse.Namespace(text=None, file=None, output=None, tui=False)
            run_json2ini_lab_logic(args)
            mock_exit.assert_called_with(1)

    @patch('main.sys.exit')
    def test_tui_launch(self, mock_exit):
        mock_agent_tui = MagicMock()
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app
        mock_exit.side_effect = SystemExit(0)

        args = argparse.Namespace(command="json2ini-lab", text=None, file=None, output=None, tui=True, project_dir=".")

        with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_agent_tui)}):
            try:
                run_json2ini_lab_logic(args)
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        mock_agent_tui.assert_called_with(project_dir=".", start_tab="tab-json2ini")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_with(0)
