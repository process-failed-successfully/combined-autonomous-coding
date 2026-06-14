import pytest
from shared.jsonl2csv_lab import Jsonl2CsvManager

class TestJsonl2CsvLab:
    def setup_method(self):
        self.manager = Jsonl2CsvManager()

    def test_flatten_simple_dict(self):
        data = {"name": "Alice", "age": 30}
        flattened = self.manager._flatten_dict(data)
        assert flattened == {"name": "Alice", "age": 30}

    def test_flatten_nested_dict(self):
        data = {"user": {"name": "Alice", "address": {"city": "Wonderland"}}}
        flattened = self.manager._flatten_dict(data)
        assert flattened == {"user.name": "Alice", "user.address.city": "Wonderland"}

    def test_flatten_with_list(self):
        data = {"name": "Alice", "hobbies": ["reading", "chess"]}
        flattened = self.manager._flatten_dict(data)
        assert flattened == {"name": "Alice", "hobbies": '["reading", "chess"]'}

    def test_convert_single_object(self):
        data = '{"name": "Alice", "age": 30}'
        csv_output = self.manager.convert(data)
        lines = csv_output.strip().split("\r\n")
        assert len(lines) == 2
        assert lines[0] == "age,name"
        assert lines[1] == "30,Alice"

    def test_convert_array_of_objects(self):
        data = '{"name": "Alice", "age": 30}\n{"name": "Bob", "age": 25}'
        csv_output = self.manager.convert(data)
        lines = csv_output.strip().split("\r\n")
        assert len(lines) == 3
        assert lines[0] == "age,name"
        assert lines[1] == "30,Alice"
        assert lines[2] == "25,Bob"

    def test_convert_array_of_objects_missing_keys(self):
        data = '{"name": "Alice"}\n{"age": 25}'
        csv_output = self.manager.convert(data)
        lines = csv_output.strip().split("\r\n")
        assert len(lines) == 3
        assert lines[0] == "age,name"
        assert lines[1] == ",Alice"
        assert lines[2] == "25,"

    def test_convert_invalid_data(self):
        with pytest.raises(ValueError, match="Invalid JSON at line 1"):
            self.manager.convert("not json")

        with pytest.raises(ValueError, match="Line 1 is valid JSON but not a JSON object"):
            self.manager.convert("123")

    def test_convert_empty_data(self):
        assert self.manager.convert("") == ""
        assert self.manager.convert("  \n   \n") == ""
