import pytest
from unittest.mock import patch, MagicMock
from io import StringIO
import sys

from shared.sitemap_lab import SitemapManager, run_sitemap_lab_logic

@pytest.fixture
def manager():
    return SitemapManager()

def test_sitemap_manager_fetch_success(manager):
    mock_response = MagicMock()
    mock_response.read.return_value = b"<urlset><url><loc>https://example.com/page.html</loc></url></urlset>"

    with patch("urllib.request.urlopen", return_value=MagicMock(__enter__=lambda _: mock_response, __exit__=lambda *args: None)):
        content = manager.fetch("https://example.com/sitemap.xml")
        assert "https://example.com/page.html" in content

def test_sitemap_manager_fetch_error(manager):
    with patch("urllib.request.urlopen", side_effect=Exception("Test Error")):
        content = manager.fetch("https://example.com/sitemap.xml")
        assert "Error fetching" in content or "Unexpected error" in content

def test_sitemap_manager_parse_urlset(manager):
    content = "<urlset><url><loc>https://example.com/1</loc></url><url><loc>https://example.com/2</loc></url></urlset>"
    result = manager.parse(content)

    assert "error" not in result
    assert result["type"] == "urlset"
    assert len(result["urls"]) == 2
    assert result["urls"][0]["loc"] == "https://example.com/1"
    assert result["urls"][1]["loc"] == "https://example.com/2"

def test_sitemap_manager_parse_sitemapindex(manager):
    content = "<sitemapindex><sitemap><loc>https://example.com/sitemap1.xml</loc></sitemap></sitemapindex>"
    result = manager.parse(content)

    assert "error" not in result
    assert result["type"] == "sitemapindex"
    assert len(result["urls"]) == 1
    assert result["urls"][0]["loc"] == "https://example.com/sitemap1.xml"

def test_sitemap_manager_parse_with_namespace(manager):
    content = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.com/ns</loc></url></urlset>'
    result = manager.parse(content)

    assert "error" not in result
    assert result["type"] == "urlset"
    assert len(result["urls"]) == 1
    assert result["urls"][0]["loc"] == "https://example.com/ns"

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

@patch("sys.stdout", new_callable=StringIO)
def test_cli_fetch(mock_stdout):
    args = MockArgs(action="fetch", url="https://example.com/sitemap.xml")

    with patch.object(SitemapManager, "fetch", return_value="<urlset/>"):
        success = run_sitemap_lab_logic(args)
        assert success is True
        assert "<urlset/>" in mock_stdout.getvalue()

@patch("sys.stdout", new_callable=StringIO)
def test_cli_parse_content(mock_stdout):
    args = MockArgs(action="parse", content="<urlset><url><loc>https://test.com</loc></url></urlset>")
    success = run_sitemap_lab_logic(args)
    assert success is True
    assert "Sitemap type: urlset" in mock_stdout.getvalue()
    assert "Total URLs found: 1" in mock_stdout.getvalue()

@patch("sys.stderr", new_callable=StringIO)
def test_cli_parse_missing_input(mock_stderr):
    args = MockArgs(action="parse")
    success = run_sitemap_lab_logic(args)
    assert success is False
    assert "must provide --file or --content" in mock_stderr.getvalue()
