import pytest
from unittest.mock import patch, MagicMock
from shared.json2java_lab import Json2JavaManager, run_json2java_lab_logic
import argparse
import sys

def test_json2java_manager_basic():
    manager = Json2JavaManager()
    json_data = '{"name": "John", "age": 30, "isActive": true}'
    result = manager.convert(json_data, "User")
    assert "public class User" in result
    assert "private String name;" in result
    assert "private Integer age;" in result
    assert "private Boolean isActive;" in result
    assert "public String getName()" in result
    assert "public void setName(String name)" in result
    assert "public Boolean getIsActive()" in result
    assert "public void setIsActive(Boolean isActive)" in result

def test_json2java_manager_nested():
    manager = Json2JavaManager()
    json_data = '{"id": 1, "address": {"street": "Main St", "city": "Anytown"}}'
    result = manager.convert(json_data, "Company")
    assert "public class Company" in result
    assert "private Address address;" in result
    assert "public class Address" in result
    assert "private String street;" in result
    assert "private String city;" in result

def test_json2java_manager_list():
    manager = Json2JavaManager()
    json_data = '{"items": [{"id": 1, "name": "Item A"}, {"id": 2, "name": "Item B"}]}'
    result = manager.convert(json_data, "Catalog")
    assert "public class Catalog" in result
    assert "private List<Item> items;" in result
    assert "public class Item" in result
    assert "private Integer id;" in result
    assert "private String name;" in result

def test_json2java_manager_invalid_json():
    manager = Json2JavaManager()
    with pytest.raises(ValueError):
        manager.convert("{invalid json")

@patch("sys.stdout")
def test_run_json2java_lab_logic_text(mock_stdout):
    args = argparse.Namespace(text='{"key": "value"}', file=None, output=None, tui=False, name="TestClass", package="com.test")
    assert run_json2java_lab_logic(args) is True

@patch("sys.stderr")
def test_run_json2java_lab_logic_empty_input(mock_stderr):
    args = argparse.Namespace(text='', file=None, output=None, tui=False)
    with patch("sys.stdin.isatty", return_value=True):
         assert run_json2java_lab_logic(args) is False
