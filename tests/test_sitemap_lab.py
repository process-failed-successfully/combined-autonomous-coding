import unittest
from unittest.mock import patch, MagicMock
from shared.sitemap_lab import SitemapManager, run_sitemap_lab_logic
import argparse

class TestSitemapLab(unittest.TestCase):

    def setUp(self):
        self.manager = SitemapManager()

    @patch('urllib.request.urlopen')
    def test_fetch_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"<urlset></urlset>"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.manager.fetch("https://example.com/sitemap.xml")
        self.assertEqual(result, "<urlset></urlset>")

    def test_fetch_invalid_url(self):
        result = self.manager.fetch("ftp://example.com")
        self.assertTrue("Error: Only http://" in result)

    def test_parse_urlset(self):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/</loc>
                <lastmod>2023-01-01</lastmod>
                <changefreq>daily</changefreq>
                <priority>1.0</priority>
            </url>
            <url>
                <loc>https://example.com/about</loc>
            </url>
        </urlset>"""

        parsed = self.manager.parse(xml_content)
        self.assertEqual(parsed["type"], "urlset")
        self.assertEqual(len(parsed["urls"]), 2)
        self.assertEqual(parsed["urls"][0]["loc"], "https://example.com/")
        self.assertEqual(parsed["urls"][0]["lastmod"], "2023-01-01")
        self.assertEqual(parsed["urls"][0]["changefreq"], "daily")
        self.assertEqual(parsed["urls"][0]["priority"], "1.0")
        self.assertEqual(parsed["urls"][1]["loc"], "https://example.com/about")

    def test_parse_sitemapindex(self):
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap>
                <loc>https://example.com/sitemap1.xml.gz</loc>
            </sitemap>
            <sitemap>
                <loc>https://example.com/sitemap2.xml.gz</loc>
            </sitemap>
        </sitemapindex>"""

        parsed = self.manager.parse(xml_content)
        self.assertEqual(parsed["type"], "sitemapindex")
        self.assertEqual(len(parsed["urls"]), 2)
        self.assertEqual(parsed["urls"][0]["loc"], "https://example.com/sitemap1.xml.gz")
        self.assertEqual(parsed["urls"][1]["loc"], "https://example.com/sitemap2.xml.gz")

    def test_parse_text(self):
        text_content = "https://example.com/\nhttps://example.com/about"
        parsed = self.manager.parse(text_content)
        self.assertEqual(parsed["type"], "text")
        self.assertEqual(len(parsed["urls"]), 2)
        self.assertEqual(parsed["urls"][0]["loc"], "https://example.com/")
        self.assertEqual(parsed["urls"][1]["loc"], "https://example.com/about")

    def test_parse_invalid_xml(self):
        parsed = self.manager.parse("<invalid_xml")
        self.assertEqual(parsed["type"], "error")

    @patch('shared.sitemap_lab.SitemapManager.fetch')
    def test_cli_fetch(self, mock_fetch):
        mock_fetch.return_value = "<urlset></urlset>"
        args = argparse.Namespace(action="fetch", url="https://example.com")

        with patch('builtins.print') as mock_print:
            success = run_sitemap_lab_logic(args)
            self.assertTrue(success)
            mock_print.assert_called_with("<urlset></urlset>")

    @patch('shared.sitemap_lab.SitemapManager.parse')
    def test_cli_parse(self, mock_parse):
        mock_parse.return_value = {
            "type": "urlset",
            "urls": [{"loc": "https://example.com"}]
        }
        args = argparse.Namespace(action="parse", file=None, content="somecontent")

        with patch('builtins.print') as mock_print:
            success = run_sitemap_lab_logic(args)
            self.assertTrue(success)
            # The last print should be the URL
            mock_print.assert_any_call("loc: https://example.com")

if __name__ == '__main__':
    unittest.main()
