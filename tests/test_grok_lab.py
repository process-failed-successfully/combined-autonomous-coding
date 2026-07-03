import pytest
from shared.grok_lab import GrokManager

@pytest.fixture
def manager():
    return GrokManager()

def test_default_patterns_loaded(manager):
    assert "IP" in manager.patterns
    assert "WORD" in manager.patterns
    assert "NUMBER" in manager.patterns
    assert "TIMESTAMP_ISO8601" in manager.patterns

def test_custom_patterns_loading():
    custom = {"CUSTOM_PATTERN": r"hello\s+world"}
    manager = GrokManager(custom)
    assert "CUSTOM_PATTERN" in manager.patterns
    assert manager.patterns["CUSTOM_PATTERN"] == r"hello\s+world"
    # Ensure defaults still exist
    assert "IP" in manager.patterns

def test_parse_valid_ip(manager):
    pattern = "%{IP:client}"
    text = "Connection from 192.168.1.1 closed."
    result = manager.parse(pattern, text)

    assert result["success"] is True
    assert "client" in result["fields"]
    assert result["fields"]["client"] == "192.168.1.1"

def test_parse_multiple_fields(manager):
    pattern = "%{IP:client} %{WORD:method} %{URIPATH:request}"
    text = "127.0.0.1 GET /index.html"
    result = manager.parse(pattern, text)

    assert result["success"] is True
    assert result["fields"]["client"] == "127.0.0.1"
    assert result["fields"]["method"] == "GET"
    assert result["fields"]["request"] == "/index.html"

def test_parse_nested_patterns(manager):
    # This assumes IPV4 is a sub-pattern, or testing we can combine
    pattern = "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}"
    text = "2023-10-25T14:30:00Z ERROR Database connection failed"
    result = manager.parse(pattern, text)

    assert result["success"] is True
    assert result["fields"]["timestamp"] == "2023-10-25T14:30:00Z"
    assert result["fields"]["level"] == "ERROR"
    assert result["fields"]["message"] == "Database connection failed"

def test_parse_no_match(manager):
    pattern = "%{IP:client}"
    text = "Connection from unknown client closed."
    result = manager.parse(pattern, text)

    assert result["success"] is False
    assert result["error"] == "No match found"

def test_parse_unknown_pattern(manager):
    pattern = "%{NOT_A_REAL_PATTERN:test}"
    text = "Some text"
    result = manager.parse(pattern, text)

    assert result["success"] is False
    assert "Unknown pattern: NOT_A_REAL_PATTERN" in result["error"]

def test_parse_unnamed_capture(manager):
    # Parsing with %{PATTERN} without name should match but not create a named field
    pattern = "%{IP} %{WORD:method}"
    text = "192.168.1.1 GET"
    result = manager.parse(pattern, text)

    assert result["success"] is True
    assert "method" in result["fields"]
    assert result["fields"]["method"] == "GET"
    # Unnamed IP should not be in fields
    assert "IP" not in result["fields"]

def test_compile_error_invalid_regex(manager):
    # If a pattern compiles to something invalid (which is hard to trigger safely in standard,
    # but let's test the error handling)
    custom = {"BAD": r"(unclosed"}
    mgr = GrokManager(custom)
    result = mgr.parse("%{BAD:bad}", "text")
    assert result["success"] is False
    assert "Generated invalid regex" in result["error"]
