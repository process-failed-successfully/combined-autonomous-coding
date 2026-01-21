import json
import pytest
from shared.mock_data import MockDataGenerator, format_json, format_csv, format_sql


@pytest.fixture
def generator():
    return MockDataGenerator()


def test_generate_int_seq(generator):
    spec = {"id": "int:seq"}
    data = generator.generate(spec, 3)
    assert len(data) == 3
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[2]["id"] == 3


def test_generate_int_range(generator):
    spec = {"age": "int:10-20"}
    data = generator.generate(spec, 5)
    for item in data:
        assert 10 <= item["age"] <= 20


def test_generate_string_name(generator):
    spec = {"name": "string:name"}
    data = generator.generate(spec, 5)
    for item in data:
        assert isinstance(item["name"], str)
        assert len(item["name"].split()) == 2


def test_generate_choice(generator):
    spec = {"role": "choice:[admin,user]"}
    data = generator.generate(spec, 10)
    for item in data:
        assert item["role"] in ["admin", "user"]


def test_format_json():
    data = [{"id": 1, "name": "Test"}]
    output = format_json(data)
    loaded = json.loads(output)
    assert loaded == data


def test_format_csv():
    data = [{"id": 1, "name": "Test"}]
    output = format_csv(data)
    assert "id,name" in output
    assert "1,Test" in output


def test_format_sql():
    data = [{"id": 1, "name": "Test", "active": True}]
    output = format_sql(data, "users")
    assert "INSERT INTO users (id, name, active) VALUES (1, 'Test', TRUE);" in output


def test_format_sql_escaping():
    data = [{"name": "O'Reilly"}]
    output = format_sql(data, "users")
    assert "INSERT INTO users (name) VALUES ('O''Reilly');" in output


def test_format_sql_invalid_table_name():
    data = [{"id": 1}]
    with pytest.raises(ValueError):
        format_sql(data, "invalid table name")
