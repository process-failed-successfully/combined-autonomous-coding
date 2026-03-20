import pytest
from pathlib import Path
from shared.api_lab import ApiLabManager

@pytest.fixture
def api_manager():
    return ApiLabManager(Path("."))

def test_generate_code_snippet_python(api_manager):
    code = api_manager.generate_code_snippet("GET", "https://api.example.com/users", "", "Python (requests)")
    assert "import requests" in code
    assert "requests.request(\"GET\"" in code
    assert "https://api.example.com/users" in code
    assert "payload =" not in code

def test_generate_code_snippet_python_with_body(api_manager):
    body = '{"name": "test"}'
    code = api_manager.generate_code_snippet("POST", "https://api.example.com/users", body, "Python (requests)")
    assert "import requests" in code
    assert "import json" in code
    assert "requests.request(\"POST\"" in code
    assert "payload = json.loads(r\"\"\"{\"name\": \"test\"}\"\"\")" in code
    assert "'Content-Type': 'application/json'" in code

def test_generate_code_snippet_nodejs(api_manager):
    code = api_manager.generate_code_snippet("GET", "https://api.example.com/users", "", "Node.js (fetch)")
    assert "const url =" in code
    assert "fetch(url, options)" in code
    assert "method: \"GET\"" in code
    assert "body:" not in code

def test_generate_code_snippet_nodejs_with_body(api_manager):
    body = '{"name": "test"}'
    code = api_manager.generate_code_snippet("POST", "https://api.example.com/users", body, "Node.js (fetch)")
    assert "method: \"POST\"" in code
    assert "body: JSON.stringify({\"name\": \"test\"})" in code
    assert "'Content-Type': 'application/json'" in code

def test_generate_code_snippet_curl(api_manager):
    code = api_manager.generate_code_snippet("GET", "https://api.example.com/users", "", "cURL")
    assert "curl -X GET" in code
    assert "\"https://api.example.com/users\"" in code
    assert "-d" not in code

def test_generate_code_snippet_curl_with_body(api_manager):
    body = '{"name": "test"}'
    code = api_manager.generate_code_snippet("POST", "https://api.example.com/users", body, "cURL")
    assert "curl -X POST" in code
    assert "-H \"Content-Type: application/json\"" in code
    assert "-d '{\"name\": \"test\"}'" in code

def test_generate_code_snippet_unsupported(api_manager):
    code = api_manager.generate_code_snippet("GET", "https://api.example.com", "", "Ruby")
    assert "Language Ruby not supported" in code
