import unittest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
import shutil
import tempfile
import sys
import yaml

from shared.docs import DocsManager

class TestDocsManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.docs_dir = self.project_dir / "docs"
        self.site_dir = self.project_dir / "site"
        self.manager = DocsManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init_creates_structure(self):
        self.manager.init()

        self.assertTrue(self.docs_dir.exists())
        self.assertTrue((self.docs_dir / "index.md").exists())
        self.assertTrue((self.docs_dir / "conf.yaml").exists())

        # Check config content
        with open(self.docs_dir / "conf.yaml", "r") as f:
            config = yaml.safe_load(f)
        self.assertIn("site_name", config)

    def test_build_generates_site(self):
        # Setup source files
        self.manager.init()
        (self.docs_dir / "extra.md").write_text("# Extra Page")
        (self.project_dir / "docs/adr").mkdir(parents=True)
        (self.project_dir / "docs/adr/001-test.md").write_text("# ADR 1")

        # Mock HealthCalculator to avoid running real checks
        with patch("shared.docs.HealthCalculator") as MockHealth:
            mock_calc = MockHealth.return_value
            mock_calc.metrics = {"test_score": 100}
            mock_calc.generate_html_report.side_effect = lambda path: path.write_text("<body><p>Report</p></body>")

            self.manager.build()

        self.assertTrue(self.site_dir.exists())
        self.assertTrue((self.site_dir / "index.html").exists())
        self.assertTrue((self.site_dir / "dashboard.html").exists())
        self.assertTrue((self.site_dir / "adrs.html").exists())
        self.assertTrue((self.site_dir / "extra.html").exists())
        self.assertTrue((self.site_dir / "adr-001-test.html").exists())

        # Check content
        index_html = (self.site_dir / "index.html").read_text()
        self.assertIn("Documentation for", index_html)

        dashboard_html = (self.site_dir / "dashboard.html").read_text()
        self.assertIn("Report", dashboard_html)

    @patch("http.server.SimpleHTTPRequestHandler")
    @patch("socketserver.TCPServer")
    def test_serve_starts_server(self, mock_server, mock_handler):
        self.manager.init()
        self.manager.build() # Ensure site dir exists

        # Mock server context manager
        server_instance = mock_server.return_value
        server_instance.__enter__.return_value = server_instance

        # Simulate KeyboardInterrupt to exit the infinite loop
        server_instance.serve_forever.side_effect = KeyboardInterrupt

        self.manager.serve(port=9999)

        mock_server.assert_called_with(("", 9999), ANY)
        server_instance.serve_forever.assert_called_once()

    def test_serve_fails_if_no_build(self):
        # Ensure site dir does not exist
        if self.site_dir.exists():
            shutil.rmtree(self.site_dir)

        with patch("builtins.print") as mock_print:
            self.manager.serve()
            mock_print.assert_called_with("❌ Site directory not found. Run 'build' first.")

if __name__ == "__main__":
    unittest.main()
