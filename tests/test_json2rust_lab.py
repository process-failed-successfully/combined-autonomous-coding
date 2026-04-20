import pytest
from shared.json2rust_lab import Json2RustManager

def test_flat_object():
    manager = Json2RustManager()
    json_str = '{"name": "Alice", "age": 30, "isActive": true}'
    result = manager.convert(json_str, root_name="User")

    assert "pub struct User {" in result
    assert "pub name: String," in result
    assert "pub age: i64," in result
    assert "pub is_active: bool," in result
    assert "}" in result

def test_nested_object():
    manager = Json2RustManager()
    json_str = '{"status": "ok", "data": {"id": 1, "value": 99.9}}'
    result = manager.convert(json_str, root_name="Response")

    assert "pub struct Response {" in result
    assert "pub status: String," in result
    assert "pub data: Data," in result

    assert "pub struct Data {" in result
    assert "pub id: i64," in result
    assert "pub value: f64," in result

def test_list_of_objects():
    manager = Json2RustManager()
    json_str = '[{"id": 1}, {"id": 2}]'
    result = manager.convert(json_str, root_name="Items")

    assert "pub struct Item {" in result
    assert "pub id: i64," in result
    assert "pub type Items = Vec<Item>;" in result

def test_invalid_json():
    manager = Json2RustManager()
    with pytest.raises(ValueError):
        manager.convert("{invalid json")

def test_empty_json_object():
    manager = Json2RustManager()
    result = manager.convert("{}", root_name="Empty")

    assert "pub struct Empty {" in result
    assert "}" in result
