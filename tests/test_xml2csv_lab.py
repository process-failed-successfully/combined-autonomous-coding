import pytest
from unittest.mock import patch, MagicMock
from shared.xml2csv_lab import Xml2CsvManager, run_xml2csv_lab_logic
import argparse
from pathlib import Path


def test_convert_xml_to_csv_empty():
    manager = Xml2CsvManager()
    assert manager.convert_xml_to_csv("") == ""
    assert manager.convert_xml_to_csv("   ") == ""


def test_convert_xml_to_csv_valid_list():
    manager = Xml2CsvManager()
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<books>
    <book>
        <title>The Great Gatsby</title>
        <author>F. Scott Fitzgerald</author>
        <year>1925</year>
    </book>
    <book>
        <title>1984</title>
        <author>George Orwell</author>
        <year>1949</year>
    </book>
</books>"""
    expected_csv = "title,author,year\r\nThe Great Gatsby,F. Scott Fitzgerald,1925\r\n1984,George Orwell,1949"

    assert manager.convert_xml_to_csv(xml_data) == expected_csv


def test_convert_xml_to_csv_single_record():
    manager = Xml2CsvManager()
    xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <title>The Great Gatsby</title>
    <author>F. Scott Fitzgerald</author>
    <year>1925</year>
</book>"""
    expected_csv = "title,author,year\r\nThe Great Gatsby,F. Scott Fitzgerald,1925"

    assert manager.convert_xml_to_csv(xml_data) == expected_csv


def test_convert_xml_to_csv_invalid():
    manager = Xml2CsvManager()
    with pytest.raises(ValueError, match="Invalid XML"):
        manager.convert_xml_to_csv("<broken><tag>")


def test_convert_xml_to_csv_no_records():
    manager = Xml2CsvManager()
    xml_data = "<?xml version='1.0'?><empty></empty>"
    assert manager.convert_xml_to_csv(xml_data) == ""

def test_convert_xml_to_csv_nested_empty():
    manager = Xml2CsvManager()
    xml_data = "<?xml version='1.0'?><empty><node></node></empty>"
    assert manager.convert_xml_to_csv(xml_data) == "node\r\n\"\""

def test_convert_xml_to_csv_no_records_valid():
    manager = Xml2CsvManager()
    # Empty list of records
    xml_data = "<?xml version='1.0'?><records><record></record></records>"
    # This evaluates to records = [{'record': ''}] from our logic, so it doesn't hit line 53


def test_run_xml2csv_lab_logic_text(capsys):
    args = argparse.Namespace(text="<r><c><k>v</k></c></r>", file=None, tui=False, action=None, output=None)
    success = run_xml2csv_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    assert "k\r\nv" in captured.out


def test_run_xml2csv_lab_logic_file(tmp_path, capsys):
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<r><c><k>v</k></c></r>")
    args = argparse.Namespace(text=None, file=str(xml_file), tui=False, action=None, output=None)
    success = run_xml2csv_lab_logic(args)
    assert success is True
    captured = capsys.readouterr()
    assert "k\r\nv" in captured.out


def test_run_xml2csv_lab_logic_file_not_found(tmp_path, capsys):
    xml_file = tmp_path / "missing.xml"
    args = argparse.Namespace(text=None, file=str(xml_file), tui=False, action=None, output=None)
    success = run_xml2csv_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_xml2csv_lab_logic_file_read_error(tmp_path, capsys):
    xml_file = tmp_path / "unreadable.xml"
    xml_file.write_text("...")
    # Change permissions to make it unreadable
    xml_file.chmod(0o000)
    args = argparse.Namespace(text=None, file=str(xml_file), tui=False, action=None, output=None)
    try:
        success = run_xml2csv_lab_logic(args)
        assert success is False
        captured = capsys.readouterr()
        assert "Error reading file" in captured.err
    finally:
        xml_file.chmod(0o644)


def test_run_xml2csv_lab_logic_output_file(tmp_path, capsys):
    out_file = tmp_path / "out.csv"
    args = argparse.Namespace(text="<r><c><k>v</k></c></r>", file=None, tui=False, action=None, output=str(out_file))
    success = run_xml2csv_lab_logic(args)
    assert success is True
    out_text = out_file.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert out_text == "k\nv"
    captured = capsys.readouterr()
    assert f"Successfully wrote to {out_file}" in captured.out


def test_run_xml2csv_lab_logic_no_input(capsys):
    # Testing branch where isatty is true (no piping) and no args
    with patch("sys.stdin.isatty", return_value=True):
        args = argparse.Namespace(text=None, file=None, tui=False, action=None, output=None)
        success = run_xml2csv_lab_logic(args)
        assert success is False
        captured = capsys.readouterr()
        assert "No input provided" in captured.err


def test_run_xml2csv_lab_logic_stdin(capsys):
    with patch("sys.stdin.isatty", return_value=False), patch("sys.stdin.read", return_value="<r><c><k>v</k></c></r>"):
        args = argparse.Namespace(text=None, file=None, tui=False, action=None, output=None)
        success = run_xml2csv_lab_logic(args)
        assert success is True
        captured = capsys.readouterr()
        assert "k\r\nv" in captured.out


def test_run_xml2csv_lab_logic_invalid_xml(capsys):
    args = argparse.Namespace(text="<broken>", file=None, tui=False, action=None, output=None)
    success = run_xml2csv_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Error: Invalid XML" in captured.err

def test_run_xml2csv_lab_logic_unexpected_output_error(capsys, tmp_path):
    # Pass a valid output path but an unwriteable directory to force Exception writing file
    out_dir = tmp_path / "protected_dir"
    out_dir.mkdir()
    out_dir.chmod(0o000)
    out_file = out_dir / "out.csv"
    args = argparse.Namespace(text="<r><c><k>v</k></c></r>", file=None, tui=False, action=None, output=str(out_file))

    try:
        success = run_xml2csv_lab_logic(args)
        assert success is False
        captured = capsys.readouterr()
        assert "Unexpected error" in captured.err
    finally:
        out_dir.chmod(0o755)


@patch('shared.xml2csv_lab.Xml2CsvManager.convert_xml_to_csv')
def test_run_xml2csv_lab_logic_unexpected_error(mock_convert, capsys):
    mock_convert.side_effect = Exception("Unexpected error")
    args = argparse.Namespace(text="<r><c><k>v</k></c></r>", file=None, tui=False, action=None, output=None)
    success = run_xml2csv_lab_logic(args)
    assert success is False
    captured = capsys.readouterr()
    assert "Unexpected error" in captured.err


@patch('shared.tui.AgentTUI')
def test_run_xml2csv_lab_logic_tui(mock_tui_class, capsys):
    # Mocking TUI execution to prevent full Textual app launch
    mock_app = MagicMock()
    mock_tui_class.return_value = mock_app

    args = argparse.Namespace(tui=True, action=None)
    success = run_xml2csv_lab_logic(args)
    assert success is True
    mock_tui_class.assert_called_once()
    mock_app.run.assert_called_once()
