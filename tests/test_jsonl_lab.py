import pytest
from shared.jsonl_lab import JsonlManager, run_jsonl_lab_logic

class DummyArgs:
    def __init__(self, action=None, input=None, output=None):
        self.action = action
        self.input = input
        self.output = output

def test_json_to_jsonl():
    manager = JsonlManager()
    json_input = '[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]'
    expected_jsonl = '{"id":1,"name":"Alice"}\n{"id":2,"name":"Bob"}'

    assert manager.json_to_jsonl(json_input) == expected_jsonl

def test_json_to_jsonl_invalid_input():
    manager = JsonlManager()
    with pytest.raises(ValueError, match="Input JSON must be an array of objects to convert to JSON Lines."):
        manager.json_to_jsonl('{"id": 1, "name": "Alice"}')

    with pytest.raises(ValueError, match="All items in the input JSON array must be objects \\(dictionaries\\)."):
        manager.json_to_jsonl('["Alice", "Bob"]')

def test_jsonl_to_json():
    manager = JsonlManager()
    jsonl_input = '{"id":1,"name":"Alice"}\n{"id":2,"name":"Bob"}'
    expected_json = '[\n  {\n    "id": 1,\n    "name": "Alice"\n  },\n  {\n    "id": 2,\n    "name": "Bob"\n  }\n]'

    assert manager.jsonl_to_json(jsonl_input, indent=2) == expected_json

def test_jsonl_to_json_invalid_input():
    manager = JsonlManager()
    jsonl_input = '{"id":1,"name":"Alice"}\nNot a JSON object'

    with pytest.raises(ValueError, match="Invalid JSON at line 2"):
        manager.jsonl_to_json(jsonl_input)

def test_validate_jsonl_valid():
    manager = JsonlManager()
    jsonl_input = '{"id":1,"name":"Alice"}\n{"id":2,"name":"Bob"}'
    is_valid, msg = manager.validate_jsonl(jsonl_input)
    assert is_valid is True
    assert msg == "Valid JSON Lines."

def test_validate_jsonl_invalid():
    manager = JsonlManager()
    jsonl_input = '{"id":1,"name":"Alice"}\n"Just a string"'
    is_valid, msg = manager.validate_jsonl(jsonl_input)
    assert is_valid is False
    assert "Line 2 is valid JSON but not a JSON object." in msg

def test_cli_logic_json2jsonl(tmp_path, capsys):
    json_file = tmp_path / "input.json"
    json_file.write_text('[{"a": 1}, {"b": 2}]')

    args = DummyArgs(action="json2jsonl", input=str(json_file))
    success = run_jsonl_lab_logic(args)
    assert success is True

    captured = capsys.readouterr()
    assert '{"a":1}\n{"b":2}' in captured.out

def test_cli_logic_jsonl2json(tmp_path, capsys):
    jsonl_file = tmp_path / "input.jsonl"
    jsonl_file.write_text('{"a": 1}\n{"b": 2}')

    args = DummyArgs(action="jsonl2json", input=str(jsonl_file))
    success = run_jsonl_lab_logic(args)
    assert success is True

    captured = capsys.readouterr()
    assert '[\n  {\n    "a": 1\n  },\n  {\n    "b": 2\n  }\n]' in captured.out

def test_cli_logic_validate(tmp_path, capsys):
    jsonl_file = tmp_path / "input.jsonl"
    jsonl_file.write_text('{"a": 1}\n{"b": 2}')

    args = DummyArgs(action="validate", input=str(jsonl_file))
    success = run_jsonl_lab_logic(args)
    assert success is True

    captured = capsys.readouterr()
    assert "Valid JSON Lines." in captured.out

def test_cli_logic_output_file(tmp_path):
    json_file = tmp_path / "input.json"
    json_file.write_text('[{"a": 1}]')
    out_file = tmp_path / "output.jsonl"

    args = DummyArgs(action="json2jsonl", input=str(json_file), output=str(out_file))
    success = run_jsonl_lab_logic(args)
    assert success is True

    assert out_file.exists()
    content = out_file.read_text()
    assert '{"a":1}' in content
