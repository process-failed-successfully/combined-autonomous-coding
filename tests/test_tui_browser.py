import unittest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from textual.app import App, ComposeResult
from shared.tui_browser import BrowserLabTab

class BrowserLabApp(App):
    CSS = """
    BrowserLabTab { height: 100%; width: 100%; }
    .stat-box { height: auto; border: solid green; }
    Input { width: 20; }
    Button { width: 10; }
    """
    def compose(self) -> ComposeResult:
        yield BrowserLabTab(project_dir=Path("."))

class TestBrowserLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_navigate(self):
        with patch("shared.tui_browser.BrowserLabManager") as MockManager:
            # Setup mock
            mock_instance = MockManager.return_value
            mock_instance.get_text = AsyncMock(return_value="Mock Text Content")
            mock_instance.get_html = AsyncMock(return_value="<html>Mock HTML</html>")

            app = BrowserLabApp()
            async with app.run_test(size=(200, 100)) as pilot:
                await pilot.pause()

                # Find input and type URL
                url_input = app.query_one("#browser-url")
                url_input.value = "https://example.com"
                await pilot.pause()

                # Click Go
                pilot.app.query_one("#btn-browser-go").press()
                await pilot.pause()
                await pilot.pause()

                # Check results
                try:
                    mock_instance.get_text.assert_called_with("https://example.com")
                    mock_instance.get_html.assert_called_with("https://example.com")

                    html_editor = app.query_one("#browser-html-editor")
                    self.assertEqual(html_editor.text, "<html>Mock HTML</html>")
                except AssertionError as e:
                    # Debug output
                    log = app.query_one("#browser-preview-log")
                    print(f"\nDEBUG: Log content: {log}")
                    raise e

    async def test_screenshot(self):
        with patch("shared.tui_browser.BrowserLabManager") as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.screenshot = AsyncMock(return_value="/tmp/shot.png")

            app = BrowserLabApp()
            async with app.run_test(size=(200, 100)) as pilot:
                await pilot.pause()
                url_input = app.query_one("#browser-url")
                url_input.value = "https://example.com"
                await pilot.pause()

                pilot.app.query_one("#btn-browser-shot").press()
                await pilot.pause()
                await pilot.pause()

                mock_instance.screenshot.assert_called()

    async def test_missing_dependency(self):
        with patch("shared.tui_browser.BrowserLabManager") as MockManager:
            mock_instance = MockManager.return_value
            mock_instance.get_text.side_effect = ImportError("No playwright")

            app = BrowserLabApp()
            async with app.run_test(size=(200, 100)) as pilot:
                await pilot.pause()
                url_input = app.query_one("#browser-url")
                url_input.value = "https://example.com"
                await pilot.pause()

                pilot.app.query_one("#btn-browser-go").press()
                await pilot.pause()
                await pilot.pause()

                # Should not crash
