import pytest
import argparse
from unittest.mock import patch
from shared.size_compare_lab import SizeCompareManager, run_size_compare_lab_logic

def test_compare_sizes_valid_json():
    manager = SizeCompareManager()
    json_data = '{"name": "test", "value": 123}'
    result = manager.compare_sizes(json_data)

    assert "Format          | Size (bytes)" in result
    assert "JSON" in result
    assert "MsgPack" in result
    assert "CBOR" in result
    assert "YAML" in result
    assert "TOML" in result
    assert "BSON" in result
    assert "XML" in result

def test_compare_sizes_invalid_json():
    manager = SizeCompareManager()
    result = manager.compare_sizes('{"invalid": json')
    assert "Error: Invalid JSON input." in result

def test_run_size_compare_lab_logic_text(capsys):
    args = argparse.Namespace(text='{"hello": "world"}', file=None)
    assert run_size_compare_lab_logic(args) == True

    captured = capsys.readouterr()
    assert "Format" in captured.out
    assert "JSON" in captured.out

def test_run_size_compare_lab_logic_file(tmp_path, capsys):
    test_file = tmp_path / "test.json"
    test_file.write_text('{"file": "test"}')

    args = argparse.Namespace(text=None, file=str(test_file))
    assert run_size_compare_lab_logic(args) == True

    captured = capsys.readouterr()
    assert "Format" in captured.out
    assert "MsgPack" in captured.out

def test_run_size_compare_lab_logic_no_input(capsys):
    args = argparse.Namespace(text=None, file=None)
    with patch('sys.stdin.isatty', return_value=True):
        assert run_size_compare_lab_logic(args) == False
        captured = capsys.readouterr()
        assert "Error: Input text or file required." in captured.err

def test_compare_sizes_non_object():
    manager = SizeCompareManager()
    json_data = '[1, 2, 3]'
    result = manager.compare_sizes(json_data)

    assert "Format          | Size (bytes)" in result
    # TOML, BSON and XML requires object root usually, or our custom function fails gracefully
    assert "N/A" in result or "Failed" in result
