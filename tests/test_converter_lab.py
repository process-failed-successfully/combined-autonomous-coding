import pytest
from shared.converter_lab import ConverterManager
import json
import xml.etree.ElementTree as ET

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
