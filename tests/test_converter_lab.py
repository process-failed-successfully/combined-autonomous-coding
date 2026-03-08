import pytest  # noqa: F401
from shared.converter_lab import ConverterManager
import json
import xml.etree.ElementTree as ET  # noqa: F401


class TestConverterManager:
    def setup_method(self):
        self.manager = ConverterManager()

    def test_convert_json_to_yaml(self):
        content = '{"key": "value", "list": [1, 2]}'
        result = self.manager.convert_format(content, "json", "yaml")
        assert "key: value" in result
        assert "list:" in result
        assert "- 1" in result

    def test_convert_yaml_to_json(self):
        content = "key: value\nlist:\n  - 1\n  - 2"
        result = self.manager.convert_format(content, "yaml", "json")
        data = json.loads(result)
        assert data["key"] == "value"
        assert data["list"] == [1, 2]

    def test_convert_to_xml(self):
        content = '{"root": {"key": "value"}}'
        result = self.manager.convert_format(content, "json", "xml")
        assert "<root>" in result
        assert "<key>value</key>" in result

    def test_parse_curl_simple(self):
        cmd = 'curl https://example.com'
        req = self.manager.parse_curl(cmd)
        assert req["url"] == "https://example.com"
        assert req["method"] == "GET"

    def test_parse_curl_post(self):
        cmd = 'curl -X POST https://api.com -H "Content-Type: application/json" -d \'{"a": 1}\''
        req = self.manager.parse_curl(cmd)
        assert req["url"] == "https://api.com"
        assert req["method"] == "POST"
        assert req["headers"]["Content-Type"] == "application/json"
        assert '{"a": 1}' in req["data"]

    def test_curl_to_python(self):
        cmd = 'curl -X POST https://api.com/users -H "Auth: Bearer 123"'
        code = self.manager.curl_to_python(cmd)
        assert "import requests" in code
        assert 'requests.post("https://api.com/users"' in code
        assert '"Auth": "Bearer 123"' in code

    def test_json_to_pydantic(self):
        json_str = '{"name": "John", "age": 30, "meta": {"active": true}}'
        code = self.manager.json_to_pydantic(json_str, "User")
        assert "class User(BaseModel):" in code
        assert "name: str" in code
        assert "age: int" in code
        assert "class UserMeta(BaseModel):" in code
        assert "meta: UserMeta" in code

    def test_json_to_typescript(self):
        json_str = '{"name": "John", "scores": [1, 2]}'
        code = self.manager.json_to_typescript(json_str, "User")
        assert "interface User {" in code
        assert "name: string;" in code
        assert "scores: number[];" in code

    def test_json_to_go(self):
        json_str = '{"user_name": "John", "age": 30, "scores": [1, 2], "meta": {"active": true}}'
        code = self.manager.json_to_go(json_str, "User")
        assert "type User struct {" in code
        assert 'UserName string `json:"user_name"`' in code
        assert 'Age int `json:"age"`' in code
        assert 'Scores []int `json:"scores"`' in code
        assert "type UserMeta struct {" in code
        assert 'Meta UserMeta `json:"meta"`' in code


import argparse  # noqa: E402
from io import StringIO  # noqa: E402
from unittest.mock import patch  # noqa: E402
from shared.converter_lab import run_converter_lab_logic  # noqa: E402


class TestConverterLabCLI:
    def setup_method(self):
        pass

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_format(self, mock_stdout):
        args = argparse.Namespace(
            action="format",
            input='{"a": 1}',
            from_fmt="json",
            to_fmt="yaml"
        )
        success = run_converter_lab_logic(args)
        assert success is True
        assert "a: 1" in mock_stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_curl(self, mock_stdout):
        args = argparse.Namespace(
            action="curl",
            input="curl https://api.example.com",
            target="python"
        )
        success = run_converter_lab_logic(args)
        assert success is True
        assert "requests.get" in mock_stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_types(self, mock_stdout):
        args = argparse.Namespace(
            action="types",
            input='{"a": 1}',
            target="typescript",
            name="MyIface"
        )
        success = run_converter_lab_logic(args)
        assert success is True
        assert "interface MyIface {" in mock_stdout.getvalue()

    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_no_action(self, mock_stdout):
        args = argparse.Namespace(action=None)
        success = run_converter_lab_logic(args)
        assert success is False
        assert "Error: No action specified" in mock_stdout.getvalue()
