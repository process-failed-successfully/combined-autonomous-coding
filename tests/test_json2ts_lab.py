import pytest
from shared.json2ts_lab import Json2TsManager

def test_flat_json():
    manager = Json2TsManager()
    json_str = '{"name": "test", "age": 30, "isActive": true}'
    result = manager.generate(json_str, root_name="User")

    assert "export interface User {" in result
    assert "name: string;" in result
    assert "age: number;" in result
    assert "isActive: boolean;" in result

def test_nested_objects():
    manager = Json2TsManager()
    json_str = '{"user": {"name": "Alice"}, "status": "ok"}'
    result = manager.generate(json_str, root_name="Response")

    assert "export interface User {" in result
    assert "name: string;" in result
    assert "export interface Response {" in result
    assert "user: User;" in result
    assert "status: string;" in result

def test_lists():
    manager = Json2TsManager()
    json_str = '{"tags": ["a", "b"], "scores": [1, 2]}'
    result = manager.generate(json_str)

    assert "tags: string[];" in result
    assert "scores: number[];" in result

def test_nested_lists():
    manager = Json2TsManager()
    json_str = '{"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}'
    result = manager.generate(json_str, root_name="Cart")

    assert "export interface ItemsItem {" in result
    assert "id: number;" in result
    assert "name: string;" in result
    assert "export interface Cart {" in result
    assert "items: ItemsItem[];" in result

def test_invalid_json():
    manager = Json2TsManager()
    with pytest.raises(ValueError):
        manager.generate("{invalid json")

def test_list_root():
    manager = Json2TsManager()
    json_str = '[{"id": 1}, {"id": 2}]'
    result = manager.generate(json_str, root_name="Item")

    assert "export interface Item {" in result
    assert "id: number;" in result

def test_sanitize_identifier():
    manager = Json2TsManager()
    json_str = '{"1st_item": "value", "class": "keyword", "a-b": 1, "_id": 1, "$id": 2}'
    result = manager.generate(json_str)

    # invalid ids get quoted
    assert '"1st_item": string;' in result
    assert '"a-b": number;' in result

    # valid ids don't get quoted
    assert "class: string;" in result
    assert "_id: number;" in result
    assert "$id: number;" in result
