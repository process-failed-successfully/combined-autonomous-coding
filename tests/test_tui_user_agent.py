import unittest
from textual.app import App, ComposeResult
from shared.tui_user_agent import UserAgentLabTab

class UserAgentLabApp(App):
    def compose(self) -> ComposeResult:
        yield UserAgentLabTab()

class TestUserAgentLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_parse_flow(self):
        app = UserAgentLabApp()
        async with app.run_test() as pilot:
            # Type UA
            input_widget = pilot.app.query_one("#ua-parse-input")
            input_widget.value = "Mozilla/5.0 (Windows NT 10.0) Chrome/99.0"

            # Click Parse
            pilot.app.query_one("#btn-ua-parse").press()
            await pilot.pause()

            # Check Table
            table = pilot.app.query_one("#ua-parse-table")
            self.assertGreater(len(table.rows), 0)

    async def test_generate_flow(self):
        app = UserAgentLabApp()
        async with app.run_test() as pilot:
            # Switch to Generate Tab
            tabs = pilot.app.query_one("TabbedContent")
            tabs.active = "ua-tab-gen"

            # Select OS
            os_select = pilot.app.query_one("#ua-gen-os")
            os_select.value = "Windows"

            # Wait for event processing (on_os_changed)
            await pilot.pause()

            # Select Browser
            browser_select = pilot.app.query_one("#ua-gen-browser")
            browser_select.value = "Chrome"

            # Click Generate
            pilot.app.query_one("#btn-ua-gen").press()
            await pilot.pause()

            # Check Output
            output = pilot.app.query_one("#ua-gen-output")
            self.assertIn("Windows", output.value)
            self.assertIn("Chrome", output.value)
