import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
from shared.excel_lab import ExcelLabManager, run_excel_lab_logic

import openpyxl

@pytest.fixture
def excel_manager(tmp_path):
    return ExcelLabManager(tmp_path)

@pytest.fixture
def sample_xlsx(tmp_path):
    file_path = tmp_path / "data.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["id", "name", "value"])
    ws.append([1, "A", 100])
    ws.append([2, "B", 200])

    ws2 = wb.create_sheet("Sheet2")
    ws2.append(["col1", "col2"])
    ws2.append(["x", "y"])

    wb.save(file_path)
    return file_path

def test_init_raises_if_no_openpyxl():
    with patch("shared.excel_lab.openpyxl", None):
        with pytest.raises(ImportError):
            ExcelLabManager()

def test_get_info(excel_manager, sample_xlsx):
    info = excel_manager.get_info(sample_xlsx)
    assert info["sheet_count"] == 2
    assert "Sheet1" in info["sheets"]
    assert "Sheet2" in info["sheets"]

def test_read_sheet_default(excel_manager, sample_xlsx):
    data = excel_manager.read_sheet(sample_xlsx)
    assert len(data) == 2
    assert data[0]["name"] == "A"
    assert data[1]["value"] == 200

def test_read_sheet_specific(excel_manager, sample_xlsx):
    data = excel_manager.read_sheet(sample_xlsx, sheet_name="Sheet2")
    assert len(data) == 1
    assert data[0]["col1"] == "x"

def test_read_sheet_not_found(excel_manager, sample_xlsx):
    with pytest.raises(ValueError, match="Sheet 'NonExistent' not found"):
        excel_manager.read_sheet(sample_xlsx, sheet_name="NonExistent")

def test_cli_info(capsys, sample_xlsx):
    args = MagicMock()
    args.action = "info"
    args.file = str(sample_xlsx)

    run_excel_lab_logic(args)
    captured = capsys.readouterr()
    assert "Sheet Count: 2" in captured.out
    assert "Sheet1" in captured.out

def test_cli_read_csv(capsys, sample_xlsx):
    args = MagicMock()
    args.action = "read"
    args.file = str(sample_xlsx)
    args.sheet = "Sheet1"
    args.format = "csv"
    args.output = None
    args.limit = 50

    run_excel_lab_logic(args)
    captured = capsys.readouterr()
    assert "id,name,value" in captured.out
    assert "1,A,100" in captured.out

def test_cli_read_json(capsys, sample_xlsx):
    args = MagicMock()
    args.action = "read"
    args.file = str(sample_xlsx)
    args.sheet = "Sheet1"
    args.format = "json"
    args.output = None
    args.limit = 50

    run_excel_lab_logic(args)
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert len(data) == 2
    assert data[0]["name"] == "A"

def test_cli_save_output(tmp_path, sample_xlsx):
    output_file = tmp_path / "out.csv"
    args = MagicMock()
    args.action = "read"
    args.file = str(sample_xlsx)
    args.sheet = "Sheet1"
    args.format = "csv"
    args.output = str(output_file)
    args.limit = 50

    run_excel_lab_logic(args)
    assert output_file.exists()
    content = output_file.read_text()
    assert "id,name,value" in content
