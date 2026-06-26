import pytest
from unittest.mock import patch, MagicMock
from shared.sec_headers_lab import SecHeadersManager
from shared.tui_sec_headers import SecHeadersLabTab
from pathlib import Path
import requests

def test_analyze_headers_all_present():
    manager = SecHeadersManager()

    mock_headers = requests.structures.CaseInsensitiveDict({
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=()"
    })

    result = manager.analyze_headers(mock_headers, "https://test.com")

    assert result["url"] == "https://test.com"
    assert result["score"] == 100
    assert result["grade"] == "A"

    for header in manager.HEADERS_TO_CHECK.keys():
        assert result["details"][header]["status"] == "Present"

def test_analyze_headers_missing_required():
    manager = SecHeadersManager()

    mock_headers = requests.structures.CaseInsensitiveDict({
        "X-Frame-Options": "DENY",
    })

    result = manager.analyze_headers(mock_headers, "https://test.com")

    assert result["score"] < 100
    assert result["details"]["Strict-Transport-Security"]["status"] == "Missing"
    assert result["details"]["Content-Security-Policy"]["status"] == "Missing"
    assert result["details"]["X-Frame-Options"]["status"] == "Present"

def test_analyze_headers_information_disclosure():
    manager = SecHeadersManager()

    mock_headers = requests.structures.CaseInsensitiveDict({
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=()",
        "X-Powered-By": "PHP/7.4.0",
        "Server": "Apache"
    })

    result = manager.analyze_headers(mock_headers, "https://test.com")

    assert result["score"] < 100
    assert "X-Powered-By" in result["details"]
    assert result["details"]["X-Powered-By"]["status"] == "Warning"
    assert "Server" in result["details"]
    assert result["details"]["Server"]["status"] == "Warning"

@patch('shared.sec_headers_lab.requests.head')
def test_analyze_url_success(mock_head):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = requests.structures.CaseInsensitiveDict({
        "Strict-Transport-Security": "max-age=31536000",
        "X-Frame-Options": "DENY"
    })
    mock_head.return_value = mock_response

    manager = SecHeadersManager()
    result = manager.analyze_url("example.com")

    mock_head.assert_called_once()
    assert result["url"] == "https://example.com"
    assert "score" in result

@patch('shared.sec_headers_lab.requests.head')
@patch('shared.sec_headers_lab.requests.get')
def test_analyze_url_fallback_to_get(mock_get, mock_head):
    mock_head_response = MagicMock()
    mock_head_response.status_code = 405
    mock_head.return_value = mock_head_response

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.headers = requests.structures.CaseInsensitiveDict({
        "Strict-Transport-Security": "max-age=31536000"
    })
    mock_get.return_value = mock_get_response

    manager = SecHeadersManager()
    result = manager.analyze_url("https://example.com")

    mock_head.assert_called_once_with("https://example.com", timeout=10, allow_redirects=True)
    mock_get.assert_called_once_with("https://example.com", timeout=10, allow_redirects=True, stream=True)
    assert result["url"] == "https://example.com"

@patch('shared.sec_headers_lab.requests.head')
def test_analyze_url_request_exception(mock_head):
    mock_head.side_effect = requests.exceptions.ConnectionError("Connection Refused")

    manager = SecHeadersManager()
    result = manager.analyze_url("https://example.com")

    assert "error" in result
    assert "Connection Refused" in result["error"]
    assert result["url"] == "https://example.com"

def test_tui_instantiation():
    # Just verify that the TUI tab can be instantiated without errors
    tab = SecHeadersLabTab(Path("/tmp"))
    assert tab.project_dir == Path("/tmp")
    assert tab.manager is not None
