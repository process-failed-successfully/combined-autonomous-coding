import unittest
import tempfile
import argparse
from pathlib import Path
from unittest.mock import patch
from io import StringIO
import tomlkit

from shared.csv2toml_lab import Csv2TomlManager, run_csv2toml_lab_logic


class TestCsv2TomlManager(unittest.TestCase):
    def setUp(self):
        self.manager = Csv2TomlManager()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_convert_valid_csv(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        toml_str = self.manager.convert(csv_data)
        doc = tomlkit.parse(toml_str)
        self.assertIn("items", doc)
        items = doc["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["name"], "Alice")
        self.assertEqual(items[0]["age"], "30")
        self.assertEqual(items[1]["name"], "Bob")
        self.assertEqual(items[1]["age"], "25")

    def test_convert_empty_csv(self):
        csv_data = ""
        toml_str = self.manager.convert(csv_data)
        self.assertEqual(toml_str, "")

    def test_convert_csv_with_semicolon_delimiter(self):
        csv_data = "name;age\nAlice;30\nBob;25"
        toml_str = self.manager.convert(csv_data, delimiter=";")
        doc = tomlkit.parse(toml_str)
        self.assertIn("items", doc)
        items = doc["items"]
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["name"], "Alice")
        self.assertEqual(items[0]["age"], "30")

    def test_process_file_valid(self):
        input_file = self.project_dir / "input.csv"
        output_file = self.project_dir / "output.toml"
        input_file.write_text("name,age\nAlice,30\nBob,25", encoding="utf-8")

        success = self.manager.process_file(input_file, output_file)
        self.assertTrue(success)
        self.assertTrue(output_file.exists())
        doc = tomlkit.parse(output_file.read_text(encoding="utf-8"))
        self.assertIn("items", doc)
        self.assertEqual(len(doc["items"]), 2)

    def test_process_file_not_found(self):
        input_file = self.project_dir / "missing.csv"
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            success = self.manager.process_file(input_file)
            self.assertFalse(success)
            self.assertIn("not found", mock_stderr.getvalue())


class TestRunCsv2TomlLabLogic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("shared.csv2toml_lab.Csv2TomlManager.process_file")
    def test_run_logic_with_file(self, mock_process_file):
        mock_process_file.return_value = True
        args = argparse.Namespace(file="test.csv", output="test.toml", delimiter=",", text=None, tui=False)
        success = run_csv2toml_lab_logic(args)
        self.assertTrue(success)
        mock_process_file.assert_called_once_with(Path("test.csv"), Path("test.toml"), delimiter=",")

    @patch("shared.csv2toml_lab.Csv2TomlManager.convert")
    def test_run_logic_with_text(self, mock_convert):
        mock_convert.return_value = '[[items]]\nname = "Alice"'
        args = argparse.Namespace(file=None, text="name\nAlice", output=None, delimiter=",", tui=False)

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            success = run_csv2toml_lab_logic(args)
            self.assertTrue(success)
            self.assertIn("Alice", mock_stdout.getvalue())

    def test_run_logic_no_input(self):
        args = argparse.Namespace(file=None, text=None, output=None, delimiter=",", tui=False)
        with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
            success = run_csv2toml_lab_logic(args)
            self.assertFalse(success)
            self.assertIn("must be provided", mock_stderr.getvalue())

    @patch("shared.csv2toml_lab.sys.exit")
    def test_run_logic_tui(self, mock_exit):
        args = argparse.Namespace(file=None, text=None, output=None, delimiter=",", tui=True, project_dir=self.project_dir)

        # In a test context, loading shared.tui can cause issues due to module cache poisoning with Textual
        # We patch sys.modules inside run_csv2toml_lab_logic via monkeypatching __import__ to verify TUI is imported.

        with patch("builtins.__import__") as mock_import:
            # We just want to prevent AgentTUI from actually trying to import/run
            mock_import.side_effect = ImportError("Mocking TUI import")

            try:
                run_csv2toml_lab_logic(args)
            except ImportError:
                pass

            # If it tried to import from shared.tui, it means it took the TUI path
            tui_import_attempted = False
            for call in mock_import.call_args_list:
                if call[0][0] == 'shared.tui':
                    tui_import_attempted = True
                    break
            self.assertTrue(tui_import_attempted)


if __name__ == "__main__":
    unittest.main()
