import pytest
import sqlite3
import os
import json
import csv
from shared.sql_lab import SqlLabManager

# Use in-memory SQLite for testing
TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def sql_manager():
    manager = SqlLabManager(TEST_DB_URL)
    # Setup initial schema and data
    manager.execute_query("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
    manager.execute_query("INSERT INTO users (name, age) VALUES ('Alice', 30)")
    manager.execute_query("INSERT INTO users (name, age) VALUES ('Bob', 25)")
    return manager

def test_execute_query_select(sql_manager):
    result = sql_manager.execute_query("SELECT * FROM users ORDER BY id")
    assert result["success"] is True
    assert result["rowcount"] == 2
    assert result["columns"] == ["id", "name", "age"]
    assert result["rows"][0]["name"] == "Alice"
    assert result["rows"][1]["name"] == "Bob"

def test_execute_query_insert(sql_manager):
    result = sql_manager.execute_query("INSERT INTO users (name, age) VALUES ('Charlie', 35)")
    assert result["success"] is True
    # SQLAlchemy result.rowcount behavior varies for INSERT with sqlite driver
    # but successful execution should be true.

    # Verify insertion
    result = sql_manager.execute_query("SELECT * FROM users WHERE name='Charlie'")
    assert result["rowcount"] == 1

def test_execute_query_error(sql_manager):
    result = sql_manager.execute_query("SELECT * FROM non_existent_table")
    assert result["success"] is False
    assert "error" in result

def test_list_tables(sql_manager):
    tables = sql_manager.list_tables()
    assert "users" in tables

def test_get_schema(sql_manager):
    schema = sql_manager.get_schema("users")
    assert "users" in schema
    columns = {c["name"]: c for c in schema["users"]}
    assert "name" in columns
    assert "age" in columns
    # Type checking might be strict string comparison, so just checking existence

def test_export_query_csv(sql_manager, tmp_path):
    output_file = tmp_path / "output.csv"
    success = sql_manager.export_query("SELECT name, age FROM users ORDER BY age", "csv", str(output_file))
    assert success is True

    with open(output_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["name"] == "Bob"
        assert rows[1]["name"] == "Alice"

def test_export_query_json(sql_manager, tmp_path):
    output_file = tmp_path / "output.json"
    success = sql_manager.export_query("SELECT name, age FROM users ORDER BY age", "json", str(output_file))
    assert success is True

    with open(output_file, "r") as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["name"] == "Bob"
        assert data[1]["name"] == "Alice"
