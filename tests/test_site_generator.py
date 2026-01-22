import unittest
import shutil
import tempfile
from pathlib import Path
from shared.site_generator import SiteGenerator

class TestSiteGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "_site"

        # Create a mock project structure
        (self.test_dir / "README.md").write_text("# Welcome\nThis is a test.", encoding="utf-8")
        (self.test_dir / "docs").mkdir()
        (self.test_dir / "docs/guide.md").write_text("# User Guide\nDo this.", encoding="utf-8")

        # Mock requirements.txt for dependencies
        (self.test_dir / "requirements.txt").write_text("flask==2.0.0\nrequests", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init(self):
        generator = SiteGenerator(self.test_dir, self.output_dir)
        self.assertEqual(generator.project_dir, self.test_dir.resolve())
        self.assertEqual(generator.output_dir, self.output_dir.resolve())

    def test_discovery(self):
        generator = SiteGenerator(self.test_dir, self.output_dir)
        pages = generator._discover_pages()

        # Should find README and docs/guide.md
        self.assertEqual(len(pages), 2)
        titles = [p["title"] for p in pages]
        self.assertIn("Introduction", titles)
        self.assertIn("Guide", titles)

    def test_build(self):
        generator = SiteGenerator(self.test_dir, self.output_dir)
        generator.build()

        # Check output files
        self.assertTrue(self.output_dir.exists())
        self.assertTrue((self.output_dir / "index.html").exists())
        self.assertTrue((self.output_dir / "dashboard.html").exists())
        self.assertTrue((self.output_dir / "dependencies.html").exists())
        self.assertTrue((self.output_dir / "docs_guide.html").exists())

        # Verify content
        index_content = (self.output_dir / "index.html").read_text(encoding="utf-8")
        self.assertIn("Welcome", index_content)
        self.assertIn("This is a test", index_content)
        self.assertIn('<nav class="sidebar">', index_content)

        dashboard_content = (self.output_dir / "dashboard.html").read_text(encoding="utf-8")
        self.assertIn("Project Dashboard", dashboard_content)

        deps_content = (self.output_dir / "dependencies.html").read_text(encoding="utf-8")
        self.assertIn("flask", deps_content)

if __name__ == "__main__":
    unittest.main()
