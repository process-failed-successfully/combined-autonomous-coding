import unittest
from unittest.mock import MagicMock, patch, mock_open
import asyncio
from pathlib import Path
from textual.widgets import Input, ListView, RichLog, Label, Button

from shared.tui_rss import RssLabTab

class TestRssLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.patcher = patch("shared.tui_rss.RssLabManager")
        self.MockManager = self.patcher.start()

        # Instantiate tab
        # We assume RssLabTab.__init__ works without full App context if we mock correctly
        self.tab = RssLabTab(self.project_dir)
        self.mock_manager = self.MockManager.return_value
        self.tab.manager = self.mock_manager

        # Mock Textual methods
        self.tab.notify = MagicMock()
        self.tab.query_one = MagicMock()

    async def asyncTearDown(self):
        self.patcher.stop()

    def test_load_feeds_empty(self):
        # Mock exists to return False
        with patch.object(Path, "exists", return_value=False):
            self.tab.load_feeds()
            self.assertEqual(self.tab.feeds, [])

    def test_load_feeds_exists(self):
        content = '["http://example.com/feed"]'
        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "read_text", return_value=content):
            self.tab.load_feeds()
            self.assertEqual(self.tab.feeds, ["http://example.com/feed"])

    async def test_add_feed(self):
        # Mock inputs
        url_input = MagicMock(spec=Input)
        url_input.value = "http://newfeed.com"

        def query_side_effect(selector, type=None):
            if selector == "#rss-new-url": return url_input
            if selector == "#rss-feed-list": return MagicMock(spec=ListView)
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock save_feeds (we don't want real file IO)
        with patch.object(self.tab, "save_feeds") as mock_save:
            await self.tab.add_feed()

            self.assertIn("http://newfeed.com", self.tab.feeds)
            mock_save.assert_called()
            self.tab.notify.assert_called_with("Added feed: http://newfeed.com")
            # Verify input cleared
            self.assertEqual(url_input.value, "")

    async def test_remove_feed(self):
        self.tab.feeds = ["http://feed1.com", "http://feed2.com"]
        self.tab.selected_feed_url = "http://feed1.com"

        def query_side_effect(selector, type=None):
            if selector == "#rss-item-list": return MagicMock(spec=ListView)
            if selector == "#rss-item-log": return MagicMock(spec=RichLog)
            if selector == "#rss-feed-list": return MagicMock(spec=ListView)
            return MagicMock() # For buttons
        self.tab.query_one.side_effect = query_side_effect

        with patch.object(self.tab, "save_feeds") as mock_save:
            self.tab.remove_feed()

            self.assertNotIn("http://feed1.com", self.tab.feeds)
            self.assertIn("http://feed2.com", self.tab.feeds)
            mock_save.assert_called()
            self.assertIsNone(self.tab.selected_feed_url)

    async def test_refresh_feed_success(self):
        self.tab.selected_feed_url = "http://feed1.com"

        lbl = MagicMock(spec=Label)
        def query_side_effect(selector, type=None):
            if selector == "#rss-feed-title": return lbl
            if selector == "#rss-item-list": return MagicMock(spec=ListView)
            return MagicMock()
        self.tab.query_one.side_effect = query_side_effect

        # Mock manager fetch
        mock_data = {
            "feed": {"title": "Test Feed"},
            "entries": [{"title": "Item 1"}, {"title": "Item 2"}]
        }
        self.mock_manager.fetch.return_value = mock_data

        await self.tab.refresh_feed()

        self.mock_manager.fetch.assert_called_with("http://feed1.com")
        self.assertEqual(self.tab.current_feed_data, mock_data)
        # Verify title update
        args_list = lbl.update.call_args_list
        # Last call should be title
        self.assertIn("Test Feed", args_list[-1][0][0])

    def test_show_item_details(self):
        log = MagicMock(spec=RichLog)
        def query_side_effect(selector, type=None):
            if selector == "#rss-item-log": return log
            return MagicMock() # For button
        self.tab.query_one.side_effect = query_side_effect

        entry = {
            "title": "Test Item",
            "link": "http://item.com",
            "published": "2023-01-01",
            "author": "Me",
            "description": "Content"
        }

        self.tab.show_item_details(entry)

        self.assertEqual(self.tab.current_link, "http://item.com")
        log.write.assert_called()
