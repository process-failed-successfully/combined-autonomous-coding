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
