import pytest
from shared.json2py_lab import Json2PyManager

def test_flat_dataclass():
    manager = Json2PyManager()
    json_str = '{"name": "test", "age": 30, "is_active": true}'
    result = manager.generate(json_str, framework="dataclass", root_name="User")

    assert "@dataclass" in result
    assert "class User:" in result
    assert "name: Optional[str] = None" in result
    assert "age: Optional[int] = None" in result
    assert "is_active: Optional[bool] = None" in result

def test_flat_pydantic():
    manager = Json2PyManager()
    json_str = '{"id": 123, "balance": 99.99}'
    result = manager.generate(json_str, framework="pydantic", root_name="Account")

    assert "class Account(BaseModel):" in result
    assert "id: Optional[int] = None" in result
    assert "balance: Optional[float] = None" in result

def test_nested_objects():
    manager = Json2PyManager()
    json_str = '{"user": {"name": "Alice"}, "status": "ok"}'
    result = manager.generate(json_str, framework="dataclass", root_name="Response")

    assert "class User:" in result
    assert "name: Optional[str] = None" in result
    assert "class Response:" in result
    assert "user: Optional[User] = None" in result
    assert "status: Optional[str] = None" in result

    # Check order: nested class should appear before root class
    assert result.index("class User:") < result.index("class Response:")

def test_lists():
    manager = Json2PyManager()
    json_str = '{"tags": ["a", "b"], "scores": [1, 2]}'
    result = manager.generate(json_str)

    assert "tags: Optional[List[str]] = None" in result
    assert "scores: Optional[List[int]] = None" in result

def test_nested_lists():
    manager = Json2PyManager()
    json_str = '{"items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}]}'
    result = manager.generate(json_str, framework="dataclass", root_name="Cart")

    assert "class ItemsItem:" in result
    assert "id: Optional[int] = None" in result
    assert "name: Optional[str] = None" in result
    assert "class Cart:" in result
    assert "items: Optional[List[ItemsItem]] = None" in result

def test_invalid_json():
    manager = Json2PyManager()
    with pytest.raises(ValueError):
        manager.generate("{invalid json")

def test_list_root():
    manager = Json2PyManager()
    json_str = '[{"id": 1}, {"id": 2}]'
    result = manager.generate(json_str, root_name="Item")

    assert "class Item:" in result
    assert "id: Optional[int] = None" in result

def test_sanitize_identifier():
    manager = Json2PyManager()
    json_str = '{"1st_item": "value", "class": "keyword", "a-b": 1}'
    result = manager.generate(json_str)

    assert "_1st_item: Optional[str] = None" in result
    assert "class_: Optional[str] = None" in result
    assert "a_b: Optional[int] = None" in result

def test_flat_msgspec():
    manager = Json2PyManager()
    json_str = '{"id": 123, "active": true}'
    result = manager.generate(json_str, framework="msgspec", root_name="User")

    assert "from msgspec import Struct" in result
    assert "class User(Struct):" in result
    assert "id: Optional[int] = None" in result
    assert "active: Optional[bool] = None" in result

def test_flat_typeddict():
    manager = Json2PyManager()
    json_str = '{"id": 123, "name": "test"}'
    result = manager.generate(json_str, framework="typeddict", root_name="User")

    assert "from typing import Any, List, Optional, TypedDict" in result
    assert "class User(TypedDict, total=False):" in result
    assert "id: int" in result
    assert "name: str" in result
