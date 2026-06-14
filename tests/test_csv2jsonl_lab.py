import pytest
import json
from shared.csv2jsonl_lab import Csv2JsonlManager

class TestCsv2JsonlLab:
    def setup_method(self):
        self.manager = Csv2JsonlManager()

    def test_convert_simple_csv(self):
        csv_data = "name,age\nAlice,30\nBob,25"
        jsonl_output = self.manager.convert(csv_data)
        lines = jsonl_output.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"name": "Alice", "age": "30"}
        assert json.loads(lines[1]) == {"name": "Bob", "age": "25"}

    def test_convert_csv_with_different_delimiter(self):
        csv_data = "name;age\nAlice;30\nBob;25"
        jsonl_output = self.manager.convert(csv_data, delimiter=';')
        lines = jsonl_output.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"name": "Alice", "age": "30"}
        assert json.loads(lines[1]) == {"name": "Bob", "age": "25"}

    def test_convert_csv_with_missing_values(self):
        csv_data = "name,age,city\nAlice,30,\nBob,,New York"
        jsonl_output = self.manager.convert(csv_data)
        lines = jsonl_output.strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"name": "Alice", "age": "30", "city": ""}
        assert json.loads(lines[1]) == {"name": "Bob", "age": "", "city": "New York"}

    def test_convert_empty_data(self):
        assert self.manager.convert("") == ""
        assert self.manager.convert("   \n   \n") == ""
