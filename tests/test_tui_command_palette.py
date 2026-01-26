import unittest
from unittest.mock import MagicMock, AsyncMock
from rich.style import Style
from textual.command import Hit
from textual.widgets import TabbedContent, TabPane, Button
from shared.tui_command_palette import NavigationProvider, ActionProvider

class TestNavigationProvider(unittest.IsolatedAsyncioTestCase):
    async def test_search_yields_hits(self):
        # Mock App
        app_mock = MagicMock()

        # Mock TabbedContent
        tabbed_content_mock = MagicMock(spec=TabbedContent)

        # Mock TabPanes
        pane1 = MagicMock(spec=TabPane)
        pane1.id = "tab-dashboard"
        pane1.title = "Dashboard"

        pane2 = MagicMock(spec=TabPane)
        pane2.id = "tab-git"
        pane2.title = "Git"

        # Need to ensure isinstance check works.
        # Since we use MagicMock(spec=TabPane), isinstance(pane1, TabPane) might fail if TabPane is not in mro.
        # But we imported TabPane.

        tabbed_content_mock.children = [pane1, pane2]

        app_mock.query_one.return_value = tabbed_content_mock

        screen_mock = MagicMock()
        screen_mock.app = app_mock
        provider = NavigationProvider(screen=screen_mock, match_style=Style())

        # Test Search "Git"
        hits = []
        async for hit in provider.search("Git"):
            hits.append(hit)

        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].text, "Go to: Git")

        # Test Action
        hits[0].command()
        # Verify tab switched
        self.assertEqual(tabbed_content_mock.active, "tab-git")

    async def test_search_no_match(self):
        app_mock = MagicMock()
        tabbed_content_mock = MagicMock(spec=TabbedContent)
        pane1 = MagicMock(spec=TabPane)
        pane1.id = "tab-dashboard"
        pane1.title = "Dashboard"
        tabbed_content_mock.children = [pane1]
        app_mock.query_one.return_value = tabbed_content_mock

        screen_mock = MagicMock()
        screen_mock.app = app_mock
        provider = NavigationProvider(screen=screen_mock, match_style=Style())

        hits = []
        async for hit in provider.search("XYZ"):
            hits.append(hit)

        self.assertEqual(len(hits), 0)


class TestActionProvider(unittest.IsolatedAsyncioTestCase):
    async def test_search_yields_actions(self):
        screen_mock = MagicMock()
        screen_mock.app = MagicMock()
        provider = ActionProvider(screen=screen_mock, match_style=Style())

        hits = []
        async for hit in provider.search("Run Tests"):
            hits.append(hit)

        self.assertTrue(len(hits) > 0)
        self.assertEqual(hits[0].text, "Global: Run Tests")

    async def test_action_execution(self):
        app_mock = MagicMock()
        screen_mock = MagicMock()
        screen_mock.app = app_mock
        provider = ActionProvider(screen=screen_mock, match_style=Style())

        # Test "Toggle Dark Mode"
        hits = []
        async for hit in provider.search("Dark Mode"):
            hits.append(hit)

        hits[0].command()
        app_mock.action_toggle_dark.assert_called_once()

        # Test "Run Tests"
        hits = []
        async for hit in provider.search("Run Tests"):
            hits.append(hit)

        # Mock button query
        btn_mock = MagicMock(spec=Button)
        app_mock.query_one.return_value = btn_mock

        hits[0].command()
        app_mock.query_one.assert_any_call("#btn-test", Button)
        btn_mock.press.assert_called_once()

if __name__ == "__main__":
    unittest.main()
