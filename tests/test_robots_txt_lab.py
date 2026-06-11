import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from shared.robots_txt_lab import RobotsTxtManager, run_robots_txt_lab_logic

@pytest.fixture
def manager():
    return RobotsTxtManager()

def test_robots_txt_manager_fetch_success(manager):
    # Mock urllib.request.urlopen
    mock_response = MagicMock()
    mock_response.read.return_value = b"User-agent: *\nDisallow: /"

    with patch("urllib.request.urlopen", return_value=MagicMock(__enter__=lambda _: mock_response, __exit__=lambda *args: None)):
        content = manager.fetch("https://example.com/robots.txt")
        assert "User-agent: *" in content
        assert "Disallow: /" in content

def test_robots_txt_manager_fetch_auto_append(manager):
    mock_response = MagicMock()
    mock_response.read.return_value = b"User-agent: Googlebot"

    with patch("urllib.request.urlopen", return_value=MagicMock(__enter__=lambda _: mock_response, __exit__=lambda *args: None)) as mock_urlopen:
        manager.fetch("https://example.com")
        # Ensure it requested /robots.txt
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://example.com/robots.txt"

def test_robots_txt_manager_fetch_error(manager):
    with patch("urllib.request.urlopen", side_effect=Exception("Test Error")):
        content = manager.fetch("https://example.com")
        assert "Error fetching" in content or "Unexpected error" in content

def test_robots_txt_manager_parse_and_check(manager):
    content = "User-agent: BadBot\nDisallow: /private\n\nUser-agent: GoodBot\nAllow: /private"

    assert manager.parse(content) is True

    assert manager.check("BadBot", "/private") is False
    assert manager.check("GoodBot", "/private") is True
    # By default, unmatched user agents should be allowed if there's no catch-all
    # But let's test a case where default is disallowed with *

    content2 = "User-agent: *\nDisallow: /\nUser-agent: SpecificBot\nAllow: /public"
    manager2 = RobotsTxtManager()
    manager2.parse(content2)

    assert manager2.check("RandomBot", "/hidden") is False
    assert manager2.check("SpecificBot", "/public") is True

class MockArgs:
    def __init__(self, action, **kwargs):
        self.action = action
        for k, v in kwargs.items():
            setattr(self, k, v)
        # default missing attrs to None
        if not hasattr(self, 'file'):
            self.file = None
        if not hasattr(self, 'content'):
            self.content = None
        if not hasattr(self, 'url'):
            self.url = None
        if not hasattr(self, 'user_agent'):
            self.user_agent = None
        if not hasattr(self, 'path'):
            self.path = None

@patch("sys.stdout", new_callable=StringIO)
def test_cli_fetch(mock_stdout):
    args = MockArgs(action="fetch", url="https://example.com/robots.txt")

    with patch.object(RobotsTxtManager, "fetch", return_value="User-agent: Test"):
        success = run_robots_txt_lab_logic(args)
        assert success is True
        assert "User-agent: Test" in mock_stdout.getvalue()

@patch("sys.stdout", new_callable=StringIO)
def test_cli_parse_content(mock_stdout):
    args = MockArgs(action="parse", content="User-agent: *")
    success = run_robots_txt_lab_logic(args)
    assert success is True
    assert "Successfully parsed" in mock_stdout.getvalue()

@patch("sys.stderr", new_callable=StringIO)
def test_cli_parse_missing_input(mock_stderr):
    args = MockArgs(action="parse")
    success = run_robots_txt_lab_logic(args)
    assert success is False
    assert "must provide --file or --content" in mock_stderr.getvalue()

@patch("sys.stdout", new_callable=StringIO)
def test_cli_check_allowed(mock_stdout):
    content = "User-agent: *\nAllow: /"
    args = MockArgs(action="check", content=content, user_agent="Bot", path="/test")
    success = run_robots_txt_lab_logic(args)
    assert success is True
    assert "ALLOWED: Bot can fetch /test" in mock_stdout.getvalue()

@patch("sys.stdout", new_callable=StringIO)
def test_cli_check_disallowed(mock_stdout):
    content = "User-agent: *\nDisallow: /"
    args = MockArgs(action="check", content=content, user_agent="Bot", path="/test")
    success = run_robots_txt_lab_logic(args)
    assert success is True
    assert "DISALLOWED: Bot cannot fetch /test" in mock_stdout.getvalue()
