import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

from shared.site_generator import SiteGenerator


class TestSiteGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_dir = self.test_dir / "my_project"
        self.project_dir.mkdir()
        self.output_dir = self.test_dir / "site_output"

        # Create dummy project files
        (self.project_dir / "README.md").write_text("# My Project\n\nThis is a test project.")
        (self.project_dir / "docs").mkdir()
        (self.project_dir / "docs" / "setup.md").write_text("# Setup\n\nInstallation steps.")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init(self):
        generator = SiteGenerator(self.project_dir)
        self.assertEqual(generator.project_dir, self.project_dir.resolve())
        self.assertEqual(generator.output_dir, self.project_dir.resolve() / "site")

    def test_scan_docs(self):
        generator = SiteGenerator(self.project_dir)
        generator._scan_docs()

        filenames = [p["filename"] for p in generator.pages]
        self.assertIn("index.html", filenames)
        self.assertIn("setup.html", filenames)

    @patch("shared.health.HealthCalculator.calculate")
    @patch("shared.dependencies.DependencyAnalyzer.scan")
    def test_generate(self, mock_scan, mock_calculate):
        # Mock dependencies to avoid actual expensive calls
        mock_calculate.return_value = None
        mock_scan.return_value = {"python": []}

        generator = SiteGenerator(self.project_dir)
        generator.generate(self.output_dir)

        # Check output directory structure
        self.assertTrue(self.output_dir.exists())
        self.assertTrue((self.output_dir / "index.html").exists())
        self.assertTrue((self.output_dir / "setup.html").exists())
        self.assertTrue((self.output_dir / "css" / "style.css").exists())
        self.assertTrue((self.output_dir / "health.html").exists())
        self.assertTrue((self.output_dir / "dependencies.html").exists())

    def test_render_markdown(self):
        generator = SiteGenerator(self.project_dir)
        md = "# Hello\n\n* List item"
        html = generator._render_markdown(md)
        self.assertIn("<h1>Hello</h1>", html)
        self.assertIn("<li>List item</li>", html)


if __name__ == "__main__":
    unittest.main()
