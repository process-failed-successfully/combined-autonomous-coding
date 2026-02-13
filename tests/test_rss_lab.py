import unittest
from unittest.mock import patch, MagicMock
import argparse
from shared.rss_lab import RssLabManager, run_rss_lab_logic


class TestRssLab(unittest.TestCase):
    def setUp(self):
        # Mock sys.exit to prevent test exit
        self.patcher_exit = patch('sys.exit')
        self.mock_exit = self.patcher_exit.start()

        # Mock rich console
        self.patcher_console = patch('shared.rss_lab.Console')
        self.mock_console_class = self.patcher_console.start()
        self.mock_console = self.mock_console_class.return_value

        self.manager = RssLabManager()
        self.manager.console = self.mock_console  # Ensure manager uses mock console

    def tearDown(self):
        self.patcher_exit.stop()
        self.patcher_console.stop()

    @patch('shared.rss_lab.feedparser.parse')
    def test_fetch_success(self, mock_parse):
        # Mock feed data
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.feed = {"title": "Test Feed", "description": "A test feed", "link": "http://example.com"}
        mock_feed.entries = [
            {"title": "Entry 1", "link": "http://example.com/1", "published": "2023-01-01"},
            {"title": "Entry 2", "link": "http://example.com/2", "published": "2023-01-02"}
        ]
        mock_parse.return_value = mock_feed

        result = self.manager.fetch("http://example.com/feed")

        self.assertEqual(result, mock_feed)
        mock_parse.assert_called_with("http://example.com/feed")

    @patch('shared.rss_lab.feedparser.parse')
    def test_display_feed(self, mock_parse):
        # Mock feed data
        mock_feed = {
            "feed": {"title": "Test Feed", "description": "Desc", "link": "Link"},
            "entries": [{"title": "Entry 1", "link": "Link 1", "published": "Date"}]
        }

        self.manager.display_feed(mock_feed)

        # Verify console print calls
        self.assertTrue(self.mock_console.print.called)

    @patch('shared.rss_lab.feedparser.parse')
    def test_inspect_feed(self, mock_parse):
        # Mock feed data
        mock_feed = {
            "feed": {"title": "Test Feed"},
            "entries": [{"title": "Entry 1"}],
            "version": "rss20"
        }

        self.manager.inspect_feed(mock_feed)
        self.assertTrue(self.mock_console.print.called)

    @patch('shared.rss_lab.RssLabManager')
    def test_cli_read(self, MockManager):
        # Mock args
        args = argparse.Namespace(action="read", url="http://example.com", limit=5)

        # Mock manager instance
        mock_instance = MockManager.return_value
        mock_instance.fetch.return_value = {"feed": {}, "entries": []}

        run_rss_lab_logic(args)

        mock_instance.fetch.assert_called_with("http://example.com")
        mock_instance.display_feed.assert_called()

    @patch('shared.rss_lab.RssLabManager')
    def test_cli_inspect(self, MockManager):
        # Mock args
        args = argparse.Namespace(action="inspect", url="http://example.com")

        # Mock manager instance
        mock_instance = MockManager.return_value
        mock_instance.fetch.return_value = {"feed": {}, "entries": []}

        run_rss_lab_logic(args)

        mock_instance.fetch.assert_called_with("http://example.com")
        mock_instance.inspect_feed.assert_called()


if __name__ == '__main__':
    unittest.main()
