import unittest
from unittest.mock import MagicMock, patch
import json
import sys
from io import StringIO
from shared.seo_lab import SeoAnalyzer, SeoLabManager, run_seo_lab_logic

class TestSeoAnalyzer(unittest.TestCase):
    def test_analyze_good_seo(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Perfect SEO Page Title</title>
            <meta name="description" content="This is a perfect meta description that is long enough to be good.">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="robots" content="index, follow">
            <link rel="canonical" href="https://example.com" />
            <meta property="og:title" content="Open Graph Title">
            <meta property="og:description" content="Open Graph Description">
            <meta property="og:image" content="image.jpg">
            <meta name="twitter:card" content="summary">
            <script type="application/ld+json">{"@context": "https://schema.org"}</script>
        </head>
        <body>
            <h1>Main Heading</h1>
            <h2>Sub Heading</h2>
            <img src="image.jpg" alt="A descriptive alt text">
            <a href="https://google.com">External Link</a>
            <a href="/internal">Internal Link</a>
        </body>
        </html>
        """
        analyzer = SeoAnalyzer()
        analyzer.feed(html)
        stats = analyzer.stats

        self.assertTrue(stats["title"]["exists"])
        self.assertEqual(stats["title"]["text"], "Perfect SEO Page Title")
        self.assertTrue(stats["meta_description"]["exists"])
        self.assertEqual(stats["h1"]["count"], 1)
        self.assertEqual(stats["h1"]["texts"][0], "Main Heading")
        self.assertEqual(stats["images"]["total"], 1)
        self.assertEqual(stats["images"]["missing_alt"], 0)
        self.assertTrue(stats["viewport"]["exists"])
        self.assertTrue(stats["canonical"]["exists"])
        self.assertTrue(stats["robots"]["exists"])
        self.assertTrue(stats["og_tags"]["title"])
        self.assertTrue(stats["structured_data"])

    def test_analyze_bad_seo(self):
        html = """
        <html>
        <head>
        </head>
        <body>
            <h1>First H1</h1>
            <h1>Second H1</h1>
            <img src="bad.jpg">
        </body>
        </html>
        """
        analyzer = SeoAnalyzer()
        analyzer.feed(html)
        stats = analyzer.stats

        self.assertFalse(stats["title"]["exists"])
        self.assertFalse(stats["meta_description"]["exists"])
        self.assertEqual(stats["h1"]["count"], 2)
        self.assertEqual(stats["images"]["total"], 1)
        self.assertEqual(stats["images"]["missing_alt"], 1)
        self.assertFalse(stats["viewport"]["exists"])

class TestSeoLabManager(unittest.TestCase):
    def setUp(self):
        self.manager = SeoLabManager()

    @patch('shared.seo_lab.urllib.request.urlopen')
    def test_analyze_url(self, mock_urlopen):
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b"<html><head><title>Test</title></head></html>"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        stats = self.manager.analyze_url("http://example.com")
        self.assertTrue(stats["title"]["exists"])
        self.assertEqual(stats["title"]["text"], "Test")

    def test_generate_report_json(self):
        stats = {
            "title": {"exists": True, "length": 4, "text": "Test"},
            "meta_description": {"exists": False, "length": 0, "content": ""},
            "h1": {"count": 1, "texts": ["H1"]},
            "h2": {"count": 0},
            "h3": {"count": 0},
            "images": {"total": 0, "missing_alt": 0, "details": []},
            "links": {"total": 0, "internal": 0, "external": 0, "broken": 0},
            "canonical": {"exists": False, "href": ""},
            "viewport": {"exists": False, "content": ""},
            "robots": {"exists": False, "content": ""},
            "og_tags": {"title": False, "description": False, "image": False},
            "twitter_tags": {"card": False},
            "structured_data": False
        }

        captured_output = StringIO()
        sys.stdout = captured_output
        try:
            self.manager.generate_report(stats, output_format="json")
        finally:
            sys.stdout = sys.__stdout__

        output = captured_output.getvalue().strip()
        self.assertIn('"exists": true', output)
        json_output = json.loads(output)
        self.assertEqual(json_output["title"]["text"], "Test")

if __name__ == '__main__':
    unittest.main()
