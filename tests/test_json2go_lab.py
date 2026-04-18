import pytest
import argparse
from shared.json2go_lab import Json2GoManager, run_json2go_lab_logic

def test_flat_object():
    manager = Json2GoManager()
    json_str = '{"name": "Alice", "age": 30, "isActive": true}'
    result = manager.convert(json_str, root_name="User")

    assert "type User struct {" in result
    assert "Name string `json:\"name\"`" in result
    assert "Age int `json:\"age\"`" in result
    assert "IsActive bool `json:\"isActive\"`" in result
    assert "}" in result

def test_nested_object():
    manager = Json2GoManager()
    json_str = '{"status": "ok", "data": {"id": 1, "value": 99.9}}'
    result = manager.convert(json_str, root_name="Response")

    assert "type Response struct {" in result
    assert "Status string `json:\"status\"`" in result
    assert "Data *Data `json:\"data\"`" in result

    assert "type Data struct {" in result
    assert "Id int `json:\"id\"`" in result
    assert "Value float64 `json:\"value\"`" in result

def test_list_of_objects():
    manager = Json2GoManager()
    json_str = '[{"id": 1}, {"id": 2}]'
    result = manager.convert(json_str, root_name="Items")

    assert "type Item struct {" in result
    assert "Id int `json:\"id\"`" in result
    assert "type Items []*Item" in result

def test_invalid_json():
    manager = Json2GoManager()
    with pytest.raises(ValueError):
        manager.convert("{invalid json")

def test_empty_json_object():
    manager = Json2GoManager()
    result = manager.convert("{}", root_name="Empty")

    assert "type Empty struct {" in result
    assert "}" in result
