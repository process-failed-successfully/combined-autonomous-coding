import pytest
import csv
import os
from pathlib import Path
from shared.csv_lab import CsvLabManager

@pytest.fixture
def csv_manager(tmp_path):
    return CsvLabManager(tmp_path)

@pytest.fixture
def sample_csv(tmp_path):
    file_path = tmp_path / "data.csv"
    data = [
        {"id": "1", "name": "Alice", "age": "30", "city": "New York"},
        {"id": "2", "name": "Bob", "age": "25", "city": "Los Angeles"},
        {"id": "3", "name": "Charlie", "age": "35", "city": "Chicago"},
        {"id": "4", "name": "David", "age": "25", "city": "Seattle"},
    ]
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return file_path

def test_load_csv(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    assert len(data) == 4
    assert data[0]["name"] == "Alice"

def test_save_csv(csv_manager, tmp_path):
    data = [{"col1": "val1", "col2": "val2"}]
    path = tmp_path / "output.csv"
    csv_manager.save_csv(data, path)

    assert path.exists()
    content = path.read_text(encoding='utf-8')
    assert "col1,col2" in content
    assert "val1,val2" in content

def test_get_headers(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    headers = csv_manager.get_headers(data)
    assert headers == ["id", "name", "age", "city"]

def test_get_stats(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    stats = csv_manager.get_stats(data)
    assert stats["rows"] == 4
    assert stats["columns"] == 4
    assert stats["empty_cells"] == 0

def test_filter_data(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)

    # Eq
    res = csv_manager.filter_data(data, "age", "25", "eq")
    assert len(res) == 2
    assert res[0]["name"] == "Bob"

    # Gt
    res = csv_manager.filter_data(data, "age", "28", "gt")
    assert len(res) == 2 # Alice (30), Charlie (35)

    # Contains
    res = csv_manager.filter_data(data, "city", "York", "contains")
    assert len(res) == 1
    assert res[0]["city"] == "New York"

def test_sort_data(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)

    # Numeric Sort (age)
    sorted_data = csv_manager.sort_data(data, "age", numeric=True)
    assert sorted_data[0]["age"] == "25"
    assert sorted_data[-1]["age"] == "35"

    # Reverse Sort (name)
    sorted_data = csv_manager.sort_data(data, "name", reverse=True)
    assert sorted_data[0]["name"] == "David"

def test_select_columns(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    selected = csv_manager.select_columns(data, ["name", "age"])

    assert len(selected) == 4
    assert list(selected[0].keys()) == ["name", "age"]
    assert "city" not in selected[0]

def test_empty_file(csv_manager, tmp_path):
    empty_path = tmp_path / "empty.csv"
    empty_path.write_text("")
    data = csv_manager.load_csv(empty_path)
    assert data == []

    stats = csv_manager.get_stats(data)
    assert stats["rows"] == 0

def test_invalid_file(csv_manager, tmp_path):
    with pytest.raises(FileNotFoundError):
        csv_manager.load_csv(tmp_path / "non_existent.csv")

def test_query_sql(csv_manager):
    # Test type inference and basic SQL execution
    data = [
        {"id": "1", "name": "Alice", "age": "30", "score": "95.5"},
        {"id": "2", "name": "Bob", "age": "25", "score": "80.0"},
        {"id": "3", "name": "Charlie", "age": "35", "score": "92.5"},
        {"id": "4", "name": "David", "age": "", "score": "null"}, # Missing/invalid data
    ]

    # Simple SELECT
    res = csv_manager.query_sql(data, "SELECT name, age FROM data WHERE age > 25")
    assert len(res) == 2
    names = [r["name"] for r in res]
    assert "Alice" in names
    assert "Charlie" in names

    # Aggregation
    res = csv_manager.query_sql(data, "SELECT AVG(score) as avg_score FROM data WHERE score != 'null'")
    assert len(res) == 1
    # (95.5 + 80.0 + 92.5) / 3 = 89.333...
    assert round(res[0]["avg_score"], 2) == 89.33

    # Order By
    res = csv_manager.query_sql(data, "SELECT name FROM data ORDER BY age DESC")
    assert len(res) == 4
    assert res[0]["name"] == "Charlie" # age 35

def test_query_sql_empty_data(csv_manager):
    res = csv_manager.query_sql([], "SELECT * FROM data")
    assert res == []

def test_query_sql_invalid_sql(csv_manager):
    data = [{"id": "1", "name": "Alice"}]
    with pytest.raises(ValueError) as excinfo:
        csv_manager.query_sql(data, "SELECT * FROM non_existent_table")
    assert "SQL Error" in str(excinfo.value)

def test_export_data_json(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    json_output = csv_manager.export_data(data, "json")
    import json
    parsed = json.loads(json_output)
    assert len(parsed) == 4
    assert parsed[0]["name"] == "Alice"

def test_export_data_markdown(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    md_output = csv_manager.export_data(data, "markdown")
    assert "| id | name | age | city |" in md_output
    assert "| --- | --- | --- | --- |" in md_output
    assert "| 1 | Alice | 30 | New York |" in md_output

def test_export_data_html(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    html_output = csv_manager.export_data(data, "html")
    assert "<table>" in html_output
    assert "<th>name</th>" in html_output
    assert "<td>Alice</td>" in html_output
    assert "</table>" in html_output

def test_export_data_invalid_format(csv_manager, sample_csv):
    data = csv_manager.load_csv(sample_csv)
    with pytest.raises(ValueError) as excinfo:
        csv_manager.export_data(data, "invalid_fmt")
    assert "Unsupported format" in str(excinfo.value)

import unittest.mock

class TestCsvLabCLI:
    @unittest.mock.patch('sys.exit', side_effect=SystemExit)
    def test_tui_action(self, mock_exit):
        from shared.csv_lab import run_csv_lab_logic
        import argparse
        import sys

        # We must properly patch the exact path being imported locally in the function
        # The function does `from shared.tui import AgentTUI`

        mock_agent_tui = unittest.mock.MagicMock()
        mock_app = unittest.mock.MagicMock()
        mock_agent_tui.return_value = mock_app

        args = argparse.Namespace(project_dir=Path("."), action="tui", file=None)

        # Create a mock module for shared.tui to avoid actually importing it
        # and raising ImportErrors on missing dependencies like PyYAML.
        mock_shared_tui = unittest.mock.MagicMock()
        mock_shared_tui.AgentTUI = mock_agent_tui

        with unittest.mock.patch.dict('sys.modules', {'shared.tui': mock_shared_tui}):
            with pytest.raises(SystemExit):
                run_csv_lab_logic(args)

        mock_agent_tui.assert_called_once_with(project_dir=Path("."), start_tab="tab-csv")
        mock_app.run.assert_called_once()
        mock_exit.assert_called_with(0)
