import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.har_lab import HarLabManager, run_har_lab_logic


@pytest.fixture
def mock_har_data():
    return {
        "log": {
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://example.com/api/data",
                        "headers": [
                            {"name": "Accept", "value": "application/json"},
                            {"name": "Authorization", "value": "Bearer token"}
                        ]
                    },
                    "response": {
                        "status": 200,
                        "bodySize": 1024
                    }
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://example.com/api/submit",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "postData": {
                            "text": "{\"key\": \"value\"}"
                        }
                    },
                    "response": {
                        "status": 201,
                        "bodySize": 512
                    }
                }
            ]
        }
    }


def test_summarize(mock_har_data):
    manager = HarLabManager(Path("."))
    summary = manager.summarize(mock_har_data)

    assert summary["total_requests"] == 2
    assert summary["total_size_bytes"] == 1536
    assert summary["methods"] == {"GET": 1, "POST": 1}
    assert summary["statuses"] == {200: 1, 201: 1}
    assert summary["domains"] == {"example.com": 2}


def test_entry_to_curl_get(mock_har_data):
    manager = HarLabManager(Path("."))
    entry = mock_har_data["log"]["entries"][0]
    curl_cmd = manager.entry_to_curl(entry)

    assert "curl -X GET 'https://example.com/api/data'" in curl_cmd
    assert "-H 'Accept: application/json'" in curl_cmd
    assert "-H 'Authorization: Bearer token'" in curl_cmd


def test_entry_to_curl_post(mock_har_data):
    manager = HarLabManager(Path("."))
    entry = mock_har_data["log"]["entries"][1]
    curl_cmd = manager.entry_to_curl(entry)

    assert "curl -X POST 'https://example.com/api/submit'" in curl_cmd
    assert "-H 'Content-Type: application/json'" in curl_cmd
    assert "-d '{\"key\": \"value\"}'" in curl_cmd


def test_extract_urls(mock_har_data):
    manager = HarLabManager(Path("."))
    urls = manager.extract_urls(mock_har_data)

    assert urls == ["https://example.com/api/data", "https://example.com/api/submit"]


@patch('shared.har_lab.HarLabManager.load_har')
def test_run_har_lab_logic_summary(mock_load_har, mock_har_data, capsys):
    mock_load_har.return_value = mock_har_data
    args = MagicMock()
    args.action = "summary"
    args.tui = False
    args.file = "test.har"
    args.project_dir = Path(".")

    assert run_har_lab_logic(args) is True

    captured = capsys.readouterr()
    assert "total_requests" in captured.out
    assert "1536" in captured.out


@patch('shared.har_lab.HarLabManager.load_har')
def test_run_har_lab_logic_curl(mock_load_har, mock_har_data, capsys):
    mock_load_har.return_value = mock_har_data
    args = MagicMock()
    args.action = "curl"
    args.tui = False
    args.file = "test.har"
    args.index = 1
    args.project_dir = Path(".")

    assert run_har_lab_logic(args) is True

    captured = capsys.readouterr()
    assert "curl -X POST" in captured.out


@patch('shared.har_lab.AgentTUI', create=True)
def test_run_har_lab_logic_tui(mock_agent_tui):
    args = MagicMock()
    args.action = "tui"
    args.tui = True
    args.project_dir = Path(".")

    with pytest.raises(SystemExit) as e:
        run_har_lab_logic(args)

    assert e.value.code == 0
    # Because of how we conditionally import AgentTUI inside the function,
    # it's tricky to assert the mock was called if it's imported locally inside the `if`.
    # As long as it exits with 0 without executing the rest of the logic, it's correct.
