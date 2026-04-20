import pytest
import argparse
from shared.json2kotlin_lab import Json2KotlinManager, run_json2kotlin_lab_logic
import json
import sys
from io import StringIO

def test_json2kotlin_manager_basic():
    manager = Json2KotlinManager()
    json_data = json.dumps({"name": "Test", "id": 123})
    result = manager.convert(json_data, "RootClass", "com.example")

    assert "package com.example" in result
    assert "data class RootClass(" in result
    assert "val name: String" in result
    assert "val id: Int" in result

def test_json2kotlin_manager_nested():
    manager = Json2KotlinManager()
    json_data = json.dumps({"user": {"name": "Test"}, "isActive": True})
    result = manager.convert(json_data, "Root", "org.test")

    assert "package org.test" in result
    assert "data class Root(" in result
    assert "val user: User" in result
    assert "val isActive: Boolean" in result
    assert "data class User(" in result
    assert "val name: String" in result

def test_json2kotlin_manager_list():
    manager = Json2KotlinManager()
    json_data = json.dumps([{"id": 1}, {"id": 2}])
    result = manager.convert(json_data, "Users", "")

    assert "data class User(" in result
    assert "val id: Int" in result
    assert "data class UsersList(val items: List<User>)" in result

def test_json2kotlin_manager_keywords():
    manager = Json2KotlinManager()
    json_data = json.dumps({"class": "A", "val": 1})
    result = manager.convert(json_data)

    assert "@com.google.gson.annotations.SerializedName(\"class\")" in result
    assert "val `class`: String" in result
    assert "@com.google.gson.annotations.SerializedName(\"val\")" in result
    assert "val `val`: Int" in result

def test_run_json2kotlin_lab_logic(monkeypatch, tmp_path):
    input_file = tmp_path / "input.json"
    input_file.write_text('{"test": "value"}')

    args = argparse.Namespace(
        file=str(input_file),
        text=None,
        name="TestObj",
        package="test",
        output=None,
        tui=False
    )

    captured_output = StringIO()
    monkeypatch.setattr(sys, "stdout", captured_output)

    success = run_json2kotlin_lab_logic(args)
    assert success

    output = captured_output.getvalue()
    assert "package test" in output
    assert "data class TestObj(" in output
    assert "val test: String" in output


def test_json2kotlin_manager_nested_collision():
    manager = Json2KotlinManager()
    json_data = json.dumps({"admin": {"user": {"name": "A"}}, "customer": {"user": {"id": 1}}})
    result = manager.convert(json_data, "Root")

    assert "data class User1(" in result
    assert "val user: User1" in result
