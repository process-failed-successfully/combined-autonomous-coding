import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
import shutil
import tempfile
import sys

from shared.docs_generator import DocsGenerator, run_docs

class TestDocsGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.test_dir / "docs/site"
        self.generator = DocsGenerator(self.test_dir, self.output_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.docs_generator.run_network_logic")
    @patch("shared.docs_generator.ADRManager")
    def test_build(self, mock_adr_manager, mock_run_network_logic):
        # Mock ADRs
        mock_instance = mock_adr_manager.return_value
        mock_instance.list_adrs.return_value = [
            {"filename": "0001-test.md", "title": "Test ADR", "status": "Accepted"}
        ]

        # Mock feature_list.json
        feature_file = self.test_dir / "feature_list.json"
        feature_file.write_text('{"features": [{"id": "1", "title": "Test Feature", "passes": true}]}', encoding="utf-8")

        # Mock history
        history_file = self.test_dir / ".agent_history"
        history_file.write_text("run-1\nrun-2", encoding="utf-8")

        # Build
        self.generator.build()

        # Check files exist
        self.assertTrue((self.output_dir / "index.html").exists())
        self.assertTrue((self.output_dir / "features.html").exists())
        self.assertTrue((self.output_dir / "architecture.html").exists())
        self.assertTrue((self.output_dir / "metrics.html").exists())
        self.assertTrue((self.output_dir / "team.html").exists())

        # Check content
        features_content = (self.output_dir / "features.html").read_text(encoding="utf-8")
        self.assertIn("Test Feature", features_content)
        self.assertIn("Passed", features_content)

        arch_content = (self.output_dir / "architecture.html").read_text(encoding="utf-8")
        self.assertIn("Test ADR", arch_content)

        # Verify network graph generation was called
        mock_run_network_logic.assert_called_once()

    def test_clean(self):
        self.output_dir.mkdir(parents=True)
        (self.output_dir / "test.html").touch()

        self.generator.clean()

        self.assertFalse(self.output_dir.exists())

    @patch("shared.docs_generator.DocsGenerator")
    def test_run_docs_build(self, mock_cls):
        args = MagicMock()
        args.project_dir = self.test_dir
        args.output = None
        args.action = "build"

        run_docs(args)

        mock_cls.assert_called_once()
        mock_cls.return_value.build.assert_called_once()

    @patch("shared.docs_generator.DocsGenerator")
    def test_run_docs_serve(self, mock_cls):
        args = MagicMock()
        args.project_dir = self.test_dir
        args.output = None
        args.action = "serve"
        args.port = 9000

        run_docs(args)

        mock_cls.assert_called_once()
        mock_cls.return_value.serve.assert_called_with(9000)

if __name__ == "__main__":
    unittest.main()
