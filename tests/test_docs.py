import unittest
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.docs import DocsManager

class TestDocsManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = DocsManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_init_site(self):
        # Action
        success = self.manager.init_site(site_name="Test Docs")

        # Assert
        self.assertTrue(success)
        self.assertTrue((self.test_dir / "mkdocs.yml").exists())
        self.assertTrue((self.test_dir / "docs" / "index.md").exists())

        # Verify content
        config = (self.test_dir / "mkdocs.yml").read_text()
        self.assertIn("site_name: Test Docs", config)

        # Test idempotency (should fail/return False if exists)
        success_retry = self.manager.init_site()
        self.assertFalse(success_retry)

    @patch("subprocess.run")
    def test_build_site(self, mock_run):
        # Action
        success = self.manager.build_site()

        # Assert
        self.assertTrue(success)
        mock_run.assert_called_with(["mkdocs", "build"], cwd=self.manager.project_dir, check=True)

    @patch("subprocess.run")
    def test_serve_site(self, mock_run):
        # Action
        self.manager.serve_site(port=9000, host="0.0.0.0")

        # Assert
        mock_run.assert_called_with(
            ["mkdocs", "serve", "--dev-addr", "0.0.0.0:9000"],
            cwd=self.manager.project_dir,
            check=True
        )

if __name__ == "__main__":
    unittest.main()
