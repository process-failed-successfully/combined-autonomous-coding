import pytest
from shared.json2java_lab import Json2JavaManager


@pytest.fixture
def manager():
    return Json2JavaManager()


def test_convert_simple_json(manager):
    json_data = '{"name": "John", "age": 30, "isActive": true}'
    result = manager.convert(json_data, root_name="Person", package_name="com.example.models")

    assert "package com.example.models;" in result
    assert "public class Person {" in result
    assert "private String name;" in result
    assert "private int age;" in result
    assert "private boolean isActive;" in result
    assert "public String getName()" in result
    assert "public int getAge()" in result
    assert "public boolean isIsActive()" in result


def test_convert_nested_json(manager):
    json_data = '{"user": {"id": 1, "username": "test"}}'
    result = manager.convert(json_data, root_name="Response")

    assert "public class Response {" in result
    assert "private User user;" in result
    assert "public class User {" in result
    assert "private int id;" in result
    assert "private String username;" in result


def test_convert_list_json(manager):
    json_data = '{"items": [{"id": 1}, {"id": 2}]}'
    result = manager.convert(json_data, root_name="Data")

    assert "import java.util.List;" in result
    assert "private List<Item> items;" in result
    assert "public class Item {" in result


def test_invalid_json(manager):
    with pytest.raises(ValueError, match="Invalid JSON"):
        manager.convert('{"invalid": json', "Root")


def test_convert_root_array(manager):
    json_data = '[{"id": 1}, {"id": 2}]'
    result = manager.convert(json_data, root_name="RootItem")

    assert "public class RootItem {" in result
    assert "private int id;" in result
    assert "public class RootWrapper {" in result
    assert "private List<RootItem> items;" in result
