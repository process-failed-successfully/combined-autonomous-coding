import pytest
from shared.json2swift_lab import Json2SwiftManager

def test_json2swift_basic():
    manager = Json2SwiftManager()
    json_data = '{"name": "Alice", "age": 30, "isActive": true}'
    result = manager.convert(json_data)

    assert "struct RootStruct: Codable {" in result
    assert "let name: String?" in result
    assert "let age: Int?" in result
    assert "let isActive: Bool?" in result

def test_json2swift_nested():
    manager = Json2SwiftManager()
    json_data = '{"user": {"id": 1, "username": "bob"}}'
    result = manager.convert(json_data)

    assert "struct RootStruct: Codable {" in result
    assert "let user: User?" in result
    assert "struct User: Codable {" in result
    assert "let id: Int?" in result
    assert "let username: String?" in result

def test_json2swift_array():
    manager = Json2SwiftManager()
    json_data = '{"tags": ["a", "b", "c"], "scores": [1, 2, 3]}'
    result = manager.convert(json_data)

    assert "struct RootStruct: Codable {" in result
    assert "let tags: [String]?" in result
    assert "let scores: [Int]?" in result

def test_json2swift_coding_keys():
    manager = Json2SwiftManager()
    json_data = '{"first_name": "Alice", "class": "A"}'
    result = manager.convert(json_data)

    assert "struct RootStruct: Codable {" in result
    assert "let firstName: String?" in result
    assert "let `class`: String?" in result
    assert "enum CodingKeys: String, CodingKey {" in result
    assert "case firstName = \"first_name\"" in result
    assert "case `class` = \"class\"" in result

def test_json2swift_root_array():
    manager = Json2SwiftManager()
    json_data = '[{"id": 1}, {"id": 2}]'
    result = manager.convert(json_data)

    assert "struct RootStructList: Codable {" in result
    assert "let items: [RootStruct]?" in result
    assert "struct RootStruct: Codable {" in result
    assert "let id: Int?" in result
