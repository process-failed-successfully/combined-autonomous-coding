import pytest
import argparse
import sys
import io
from shared.json2csharp_lab import Json2CSharpManager, run_json2csharp_lab_logic

def test_json2csharp_manager_simple():
    manager = Json2CSharpManager()
    json_str = '{"name": "John", "age": 30, "isActive": true}'
    result = manager.convert(json_str, "User")

    assert "public class User" in result
    assert "public string Name { get; set; }" in result
    assert "public int Age { get; set; }" in result
    assert "public bool IsActive { get; set; }" in result
    assert "using System;" in result
    assert "namespace MyNamespace" in result

def test_json2csharp_manager_nested():
    manager = Json2CSharpManager()
    json_str = '{"user": {"name": "John", "id": 123}, "status": "active"}'
    result = manager.convert(json_str, "Root", "TestNamespace")

    assert "namespace TestNamespace" in result
    assert "public class Root" in result
    assert "public User User { get; set; }" in result
    assert "public class User" in result
    assert "public string Name { get; set; }" in result
    assert "public int Id { get; set; }" in result
    assert "public string Status { get; set; }" in result

def test_json2csharp_manager_list():
    manager = Json2CSharpManager()
    json_str = '[{"name": "John"}, {"name": "Jane"}]'
    result = manager.convert(json_str, "User")

    assert "public class User" in result
    assert "public string Name { get; set; }" in result
    assert "public class UserList" in result
    assert "public List<User> Items { get; set; }" in result

def test_json2csharp_manager_invalid_json():
    manager = Json2CSharpManager()
    with pytest.raises(ValueError, match="Invalid JSON"):
        manager.convert("{invalid json}")

def test_run_json2csharp_lab_logic(monkeypatch):
    args = argparse.Namespace(
        text='{"test": 123}',
        name="TestClass",
        namespace="TestNamespace",
        file=None,
        output=None,
        tui=False
    )

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', captured_out)

    success = run_json2csharp_lab_logic(args)
    assert success is True

    output = captured_out.getvalue()
    assert "public class TestClass" in output
    assert "public int Test { get; set; }" in output
    assert "namespace TestNamespace" in output

def test_run_json2csharp_lab_logic_empty_input():
    args = argparse.Namespace(
        text="",
        name="TestClass",
        namespace="TestNamespace",
        file=None,
        output=None,
        tui=False
    )
    success = run_json2csharp_lab_logic(args)
    assert success is False
