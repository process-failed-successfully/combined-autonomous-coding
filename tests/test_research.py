import unittest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import subprocess

from shared.research import ResearchManager, run_research_logic

class TestResearchManager(unittest.TestCase):
    @patch("shared.research.shutil.which")
    @patch("shared.research.KnowledgeManager")
    def setUp(self, mock_km, mock_which):
        mock_which.return_value = "/usr/bin/lynx"
        self.mock_km = mock_km
        self.manager = ResearchManager()

    @patch("subprocess.run")
    def test_fetch_page_text_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="Page Content")

        content = self.manager.fetch_page_text("http://example.com")
        self.assertEqual(content, "Page Content")

        # Verify call args
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "/usr/bin/lynx")
        self.assertIn("-dump", args)
        self.assertIn("http://example.com", args)

    @patch("subprocess.run")
    def test_fetch_page_text_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, ["lynx"], stderr="Error")

        content = self.manager.fetch_page_text("http://example.com")
        self.assertEqual(content, "")

    @patch("subprocess.run")
    def test_extract_links(self, mock_run):
        output = """
        References

        1. http://example.com/page1
        2. https://google.com
        3. relative/path (lynx usually resolves these but just in case)
        """
        mock_run.return_value = MagicMock(returncode=0, stdout=output)

        links = self.manager.extract_links("http://example.com")
        self.assertEqual(len(links), 2)
        self.assertIn("http://example.com/page1", links)
        self.assertIn("https://google.com", links)

    @patch("shared.research.ResearchManager.fetch_page_text")
    @patch("shared.research.ResearchManager.extract_links")
    def test_crawl_depth_0(self, mock_extract, mock_fetch):
        # Decorators are applied bottom-up. extract_links is inner, so it corresponds to first arg?
        # No, top-down order for args.
        # @patch(A)
        # @patch(B)
        # def test(self, mock_A, mock_B)

        mock_fetch.return_value = "Content"
        # Depth 0 should not extract links

        results = self.manager.crawl("http://start.com", depth=0)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["url"], "http://start.com")
        self.assertEqual(results[0]["content"], "Content")

        mock_extract.assert_not_called()

        # Verify save
        self.manager.knowledge_manager.add_knowledge.assert_called_once()

    @patch("shared.research.ResearchManager.fetch_page_text")
    @patch("shared.research.ResearchManager.extract_links")
    def test_crawl_depth_1(self, mock_extract, mock_fetch):
        # Mock responses based on URL
        def fetch_side_effect(url):
            return f"Content of {url}"
        mock_fetch.side_effect = fetch_side_effect

        mock_extract.return_value = ["http://start.com/subpage"]

        results = self.manager.crawl("http://start.com", depth=1)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["url"], "http://start.com")
        self.assertEqual(results[1]["url"], "http://start.com/subpage")

        # Check that it saves both
        self.assertEqual(self.manager.knowledge_manager.add_knowledge.call_count, 2)

    @patch("shared.research.ResearchManager.fetch_page_text")
    @patch("shared.research.ResearchManager.extract_links")
    def test_crawl_limit(self, mock_extract, mock_fetch):
        mock_fetch.return_value = "Content"
        # Must match domain of start url
        mock_extract.return_value = ["http://start.com/a", "http://start.com/b", "http://start.com/c"]

        # Limit 2: Start + 1 child
        results = self.manager.crawl("http://start.com", depth=1, limit=2)

        self.assertEqual(len(results), 2)

if __name__ == "__main__":
    unittest.main()
