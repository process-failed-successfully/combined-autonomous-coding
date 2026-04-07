import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.md2csv_lab import Md2CsvManager, run_md2csv_lab_logic

@pytest.fixture
def manager():
    return Md2CsvManager()

def test_md2csv_basic(manager):
    md_data = """
| Name | Age |
|---|---|
| Alice | 30 |
| Bob | 25 |
"""
    expected = "Name,Age\r\nAlice,30\r\nBob,25\r\n"
    assert manager.convert_to_csv(md_data) == expected

def test_md2csv_no_separator(manager):
    md_data = """
| Header 1 | Header 2 |
| Value 1 | Value 2 |
"""
    expected = "Header 1,Header 2\r\nValue 1,Value 2\r\n"
    assert manager.convert_to_csv(md_data) == expected

def test_md2csv_custom_delimiter(manager):
    md_data = """
| Col1 | Col2 |
|---|---|
| A | B |
"""
    expected = "Col1;Col2\r\nA;B\r\n"
    assert manager.convert_to_csv(md_data, delimiter=";") == expected

def test_md2csv_empty_input(manager):
    assert manager.convert_to_csv("") == ""
    assert manager.convert_to_csv("  \n  ") == ""

def test_md2csv_no_pipes(manager):
    md_data = "Just some text\nwithout pipes"
    assert manager.convert_to_csv(md_data) == ""

def test_md2csv_whitespace_trimming(manager):
    md_data = "|  Spaced  |   Out   |\n|---|---|\n|  1  |  2  |"
    expected = "Spaced,Out\r\n1,2\r\n"
    assert manager.convert_to_csv(md_data) == expected

@patch('builtins.print')
def test_cli_text_input(mock_print):
    args = MagicMock()
    args.tui = False
    args.action = None
    args.file = None
    args.text = "| A | B |\n|---|---|\n| 1 | 2 |"
    args.output = None
    args.delimiter = ","

    assert run_md2csv_lab_logic(args) is True
    mock_print.assert_called_with("A,B\r\n1,2\r\n")

@patch('builtins.print')
def test_cli_file_input(mock_print, tmp_path):
    md_file = tmp_path / "input.md"
    md_file.write_text("| X | Y |\n|---|---|\n| 9 | 8 |")

    args = MagicMock()
    args.tui = False
    args.action = None
    args.file = str(md_file)
    args.text = None
    args.output = None
    args.delimiter = ","

    assert run_md2csv_lab_logic(args) is True
    mock_print.assert_called_with("X,Y\r\n9,8\r\n")

@patch('builtins.print')
def test_cli_file_output(mock_print, tmp_path):
    args = MagicMock()
    args.tui = False
    args.action = None
    args.file = None
    args.text = "| M | N |\n|---|---|\n| 5 | 6 |"
    out_file = tmp_path / "output.csv"
    args.output = str(out_file)
    args.delimiter = ","

    assert run_md2csv_lab_logic(args) is True
    assert out_file.read_text().replace("\r\n", "\n") == "M,N\n5,6\n"
    mock_print.assert_called_with(f"✅ Successfully wrote CSV data to '{str(out_file)}'.")

@patch('shared.md2csv_lab.sys.stdin.isatty', return_value=True)
@patch('builtins.print')
def test_cli_no_input(mock_print, mock_isatty):
    args = MagicMock()
    args.tui = False
    args.action = None
    args.file = None
    args.text = None
    args.output = None
    args.delimiter = ","

    assert run_md2csv_lab_logic(args) is False
    mock_print.assert_called_with("Error: No input provided. Use --file, --text, or stdin.", file=sys.stderr)

@patch('shared.md2csv_lab.sys.exit')
@patch('shared.md2csv_lab.AgentTUI', create=True)
def test_cli_tui_mode(mock_tui, mock_exit):
    mock_app = MagicMock()
    mock_tui.return_value = mock_app

    args = MagicMock()
    args.tui = True
    args.action = None

    # We patch sys.exit and patch the local import of AgentTUI
    with patch.dict('sys.modules', {'shared.tui': MagicMock(AgentTUI=mock_tui)}):
        run_md2csv_lab_logic(args)

    mock_tui.assert_called_once()
    mock_app.run.assert_called_once()
    mock_exit.assert_called_once_with(0)
