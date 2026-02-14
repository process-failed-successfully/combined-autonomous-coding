import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from io import StringIO
from pathlib import Path

# Import the module to test
from shared.browser_lab import BrowserLabManager, run_browser_lab_logic

class TestBrowserLab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Redirect stdout/stderr
        self.held_stdout = StringIO()
        self.held_stderr = StringIO()
        sys.stdout = self.held_stdout
        sys.stderr = self.held_stderr

    def tearDown(self):
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    @patch("shared.browser_lab.async_playwright")
    async def test_manager_screenshot(self, mock_playwright):
        # Setup mock
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value

        manager = BrowserLabManager()
        await manager.screenshot("http://example.com", "out.png")

        # Verify calls
        mock_p.chromium.launch.assert_called_with(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        mock_page.goto.assert_called_with("http://example.com")
        mock_page.screenshot.assert_called_with(path="out.png", full_page=True)
        mock_browser.close.assert_called_once()

    @patch("shared.browser_lab.async_playwright")
    async def test_manager_pdf(self, mock_playwright):
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value

        manager = BrowserLabManager()
        await manager.pdf("http://example.com", "out.pdf")

        mock_page.pdf.assert_called_with(path="out.pdf")

    @patch("shared.browser_lab.async_playwright")
    async def test_manager_evaluate(self, mock_playwright):
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value
        mock_page.evaluate.return_value = 42

        manager = BrowserLabManager()
        res = await manager.evaluate("http://example.com", "1+1")

        self.assertEqual(res, 42)
        mock_page.evaluate.assert_called_with("1+1")

    @patch("shared.browser_lab.async_playwright")
    async def test_manager_inspect(self, mock_playwright):
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p
        mock_browser = mock_p.chromium.launch.return_value
        mock_context = mock_browser.new_context.return_value
        mock_page = mock_context.new_page.return_value

        mock_page.title.return_value = "Test Title"
        mock_page.url = "http://example.com"

        # FIX: Make locator synchronous
        mock_page.locator = MagicMock()
        mock_locator = MagicMock()
        mock_page.locator.return_value = mock_locator

        # Mock meta tags
        meta1 = AsyncMock()
        meta1.get_attribute.side_effect = lambda x: "description" if x == "name" else "A test page"

        # locator.all() returns list
        mock_locator.all.return_value = [meta1]

        manager = BrowserLabManager()
        res = await manager.inspect("http://example.com")

        self.assertEqual(res["title"], "Test Title")
        self.assertEqual(res["url"], "http://example.com")
        self.assertEqual(res["meta"], [{"description": "A test page"}])

    @patch("shared.browser_lab.async_playwright")
    async def test_cli_screenshot(self, mock_playwright):
        mock_p = AsyncMock()
        mock_playwright.return_value.__aenter__.return_value = mock_p

        args = MagicMock()
        args.action = "screenshot"
        args.url = "http://example.com"
        args.output = "test.png"
        args.viewport = False

        await run_browser_lab_logic(args)

        output = self.held_stdout.getvalue()
        self.assertIn("Screenshot saved to test.png", output)

    def test_missing_playwright(self):
        # Simulate missing playwright
        with patch("shared.browser_lab.async_playwright", None):
            manager = BrowserLabManager()

            # Since _check_deps is called inside the methods
            # We can't check async raise easily without await
            # But we can verify CLI logic if we wrap it?
            pass
            # Skipping strictly because IsolatedAsyncioTestCase mixed with sync patching of module globals
            # can be tricky. But let's try.

    async def test_missing_playwright_async(self):
         with patch("shared.browser_lab.async_playwright", None):
            args = MagicMock()
            args.action = "text"
            args.url = "http://example.com"
            args.output = None

            with self.assertRaises(SystemExit) as cm:
                await run_browser_lab_logic(args)
            self.assertEqual(cm.exception.code, 1)

            err = self.held_stderr.getvalue()
            self.assertIn("Playwright is not installed", err)

if __name__ == "__main__":
    unittest.main()
