import unittest
import json
import argparse
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.csv2json_lab import Csv2JsonManager, run_csv2json_lab_logic

class TestCsv2JsonLab(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2JsonManager()

    def test_convert_simple_csv(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        json_output = self.manager.convert(csv_data)
        data = json.loads(json_output)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        self.assertEqual(data[0]["age"], "30")
        self.assertEqual(data[1]["name"], "Bob")
        self.assertEqual(data[1]["age"], "25")

    def test_convert_custom_delimiter(self):
        csv_data = "name;age\nAlice;30\nBob;25"
        json_output = self.manager.convert(csv_data, delimiter=";")
        data = json.loads(json_output)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        self.assertEqual(data[0]["age"], "30")

    def test_convert_empty_file(self):
        csv_data = ""
        json_output = self.manager.convert(csv_data)
        data = json.loads(json_output)
        self.assertEqual(data, [])

    def test_convert_only_headers(self):
        csv_data = "name,age\n"
        json_output = self.manager.convert(csv_data)
        data = json.loads(json_output)
        self.assertEqual(data, [])

    def test_convert_missing_columns(self):
        csv_data = "name,age\nAlice\nBob,25"
        json_output = self.manager.convert(csv_data)
        data = json.loads(json_output)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Alice")
        # csv.DictReader provides None for missing values, which our manager maps to ""
        self.assertEqual(data[0]["age"], "")
        self.assertEqual(data[1]["name"], "Bob")
        self.assertEqual(data[1]["age"], "25")

    @patch('sys.exit')
    def test_run_logic_tui(self, mock_exit):
        mock_exit.side_effect = SystemExit
        args = argparse.Namespace(project_dir=Path("."), tui=True, file=None, action=None)

        mock_agent_tui = MagicMock()
        mock_app = MagicMock()
        mock_agent_tui.return_value = mock_app

        mock_shared_tui = MagicMock()
        mock_shared_tui.AgentTUI = mock_agent_tui

        with patch.dict('sys.modules', {'shared.tui': mock_shared_tui}):
            with self.assertRaises(SystemExit):
                run_csv2json_lab_logic(args)

        mock_agent_tui.assert_called_once_with(project_dir=Path("."), start_tab="tab-csv2json")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_with(0)

if __name__ == '__main__':
    unittest.main()
