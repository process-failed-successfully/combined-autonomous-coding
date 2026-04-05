import pytest
import io
import sys
import argparse
from unittest.mock import patch, mock_open

from shared.json2sql_lab import Json2SqlManager, run_json2sql_lab_logic


def test_json2sql_manager_valid_json_string():
    manager = Json2SqlManager()
    json_data = '[{"id": 1, "name": "Alice"}]'
    result = manager.convert(json_data, "users")
    assert result == "INSERT INTO users (id, name) VALUES ('1', 'Alice');"


def test_json2sql_manager_valid_json_dict():
    manager = Json2SqlManager()
    json_data = {"id": 2, "name": "Bob"}
    result = manager.convert(json_data, "users")
    assert result == "INSERT INTO users (id, name) VALUES ('2', 'Bob');"


def test_json2sql_manager_invalid_json_string():
    manager = Json2SqlManager()
    json_data = "invalid json"
    with pytest.raises(ValueError, match="Invalid JSON string:"):
        manager.convert(json_data, "users")


def test_json2sql_manager_invalid_data_type():
    manager = Json2SqlManager()
    json_data = 123
    with pytest.raises(ValueError, match="JSON data must be an object or an array of objects."):
        manager.convert(json_data, "users")


def test_json2sql_manager_empty_data():
    manager = Json2SqlManager()
    assert manager.convert("[]", "users") == ""
    assert manager.convert("", "users") == ""
    assert manager.convert("{}", "users") == ""


def test_json2sql_manager_complex_types():
    manager = Json2SqlManager()
    json_data = [{"id": 1, "data": {"key": "value"}, "tags": ["a", "b"], "active": True, "null_val": None}]
    result = manager.convert(json_data, "mixed_table")
    assert "INSERT INTO mixed_table (id, data, tags, active, null_val) VALUES" in result
    assert "'1'" in result
    assert "'{\"key\": \"value\"}'" in result
    assert "'[\"a\", \"b\"]'" in result
    assert "TRUE" in result
    assert "NULL" in result


def test_json2sql_manager_escape_quotes():
    manager = Json2SqlManager()
    json_data = [{"id": 1, "name": "O'Connor"}]
    result = manager.convert(json_data, "users")
    assert result == "INSERT INTO users (id, name) VALUES ('1', 'O''Connor');"


def test_run_json2sql_lab_logic_text_arg(capsys):
    args = argparse.Namespace(
        text='[{"id": 1, "name": "Test"}]',
        table="test_table",
        file=None,
        output=None,
        tui=False
    )
    success = run_json2sql_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    assert "INSERT INTO test_table (id, name) VALUES ('1', 'Test');" in captured.out


@patch('builtins.open', new_callable=mock_open, read_data='[{"id": 2}]')
def test_run_json2sql_lab_logic_file_arg(mock_file, capsys):
    args = argparse.Namespace(
        text=None,
        file="input.json",
        table="file_table",
        output=None,
        tui=False
    )
    success = run_json2sql_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    assert "INSERT INTO file_table (id) VALUES ('2');" in captured.out


@patch('sys.stdin.isatty', return_value=False)
@patch('sys.stdin.read', return_value='[{"id": 3}]')
def test_run_json2sql_lab_logic_stdin(mock_read, mock_isatty, capsys):
    args = argparse.Namespace(
        text=None,
        file=None,
        table="stdin_table",
        output=None,
        tui=False
    )
    success = run_json2sql_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    assert "INSERT INTO stdin_table (id) VALUES ('3');" in captured.out


def test_run_json2sql_lab_logic_no_input(capsys):
    args = argparse.Namespace(
        text=None,
        file=None,
        table="test_table",
        output=None,
        tui=False
    )
    with patch('sys.stdin.isatty', return_value=True):
        success = run_json2sql_lab_logic(args)

    assert success is False
    captured = capsys.readouterr()
    assert "Error: No input provided" in captured.err


def test_run_json2sql_lab_logic_tui():
    real_import = __builtins__['__import__']

    def mock_import(name, *args, **kwargs):
        if name == 'shared.tui':
            from unittest.mock import MagicMock
            return MagicMock()
        return real_import(name, *args, **kwargs)

    args = argparse.Namespace(
        tui=True,
        project_dir=None
    )

    with patch('builtins.__import__', side_effect=mock_import):
        with patch('asyncio.get_running_loop', side_effect=RuntimeError('no loop')):
            success = run_json2sql_lab_logic(args)

    assert success is True
