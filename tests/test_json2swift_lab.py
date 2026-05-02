import pytest
import unittest
from unittest.mock import patch
import io
import argparse
import sys

from shared.json2swift_lab import Json2SwiftManager, run_json2swift_lab_logic

class TestJson2SwiftManager:
    @pytest.fixture
    def manager(self):
        return Json2SwiftManager()

    def test_basic_conversion(self, manager):
        json_data = '{"name": "Alice", "age": 30, "isActive": true}'
        swift_code = manager.convert(json_data, "User")

        assert "struct User: Codable {" in swift_code
        assert "var name: String?" in swift_code
        assert "var age: Int?" in swift_code
        assert "var isActive: Bool?" in swift_code

    def test_nested_objects(self, manager):
        json_data = '{"user": {"name": "Bob"}}'
        swift_code = manager.convert(json_data, "Response")

        assert "struct User: Codable {" in swift_code
        assert "struct Response: Codable {" in swift_code
        assert "var user: User?" in swift_code

    def test_lists(self, manager):
        json_data = '{"items": [{"id": 1}], "tags": ["a", "b"]}'
        swift_code = manager.convert(json_data, "Data")

        assert "struct Item: Codable {" in swift_code
        assert "var items: [Item]?" in swift_code
        assert "var tags: [String]?" in swift_code

    def test_invalid_json(self, manager):
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.convert('{"bad": json')

    def test_coding_keys(self, manager):
        json_data = '{"first_name": "Alice", "Last-Name": "Smith"}'
        swift_code = manager.convert(json_data, "User")

        assert "var firstName: String?" in swift_code
        assert "var lastName: String?" in swift_code
        assert "enum CodingKeys: String, CodingKey {" in swift_code
        assert 'case firstName = "first_name"' in swift_code
        assert 'case lastName = "Last-Name"' in swift_code

def test_run_json2swift_lab_logic_cli_stdout():
    args = argparse.Namespace(action=None, text='{"key": "value"}', file=None, name="MyStruct", output=None, tui=False)
    with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
        success = run_json2swift_lab_logic(args)

    assert success is True
    output = mock_stdout.getvalue()
    assert "struct MyStruct: Codable {" in output
    assert "var key: String?" in output
