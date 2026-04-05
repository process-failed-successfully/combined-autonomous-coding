import unittest
from unittest.mock import MagicMock, patch
from shared.tui_mac import MacLabTab
from textual.app import App
from textual.widgets import TabbedContent
from shared.mac_lab import MacLabManager

class DummyApp(App):
    def compose(self):
        yield MacLabTab()

    async def on_mount(self):
        # Allow notify calls without erroring
        self.notify = MagicMock()

class TestMacLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_generate_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            # We must ensure the correct tab is active before clicking its buttons
            tabs = app.query_one(TabbedContent)
            tabs.active = "mac-tab-generate"
            await pilot.pause()

            app.query_one("#mac-gen-count").value = "2"
            app.query_one("#mac-gen-prefix").value = "00:1A:2B"
            app.query_one("#mac-gen-format").value = "hyphen"

            with patch('shared.tui_mac.MacLabManager.generate', return_value=["00-1A-2B-CC-DD-EE"]) as mock_generate:
                app.query_one("#btn-mac-generate").press()
        await pilot.pause()
                mock_generate.assert_called_once_with(count=2, prefix="00:1A:2B", format="hyphen")
                log = app.query_one("#mac-gen-result")
                self.assertTrue(any("00-1A-2B-CC-DD-EE" in line.text for line in log.lines))

    async def test_format_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "mac-tab-format"
            await pilot.pause()

            app.query_one("#mac-fmt-input").value = "001122334455"
            app.query_one("#mac-fmt-format").value = "hyphen"

            with patch('shared.tui_mac.MacLabManager.format', return_value="00-11-22-33-44-55") as mock_format:
                app.query_one("#btn-mac-format").press()
        await pilot.pause()
                mock_format.assert_called_once_with("001122334455", "hyphen")

    async def test_validate_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "mac-tab-validate"
            await pilot.pause()

            app.query_one("#mac-val-input").value = "invalid"

            with patch('shared.tui_mac.MacLabManager.validate', return_value=False) as mock_validate:
                app.query_one("#btn-mac-validate").press()
        await pilot.pause()
                mock_validate.assert_called_once_with("invalid")

    async def test_lookup_action(self):
        app = DummyApp()
        async with app.run_test() as pilot:
            tabs = app.query_one(TabbedContent)
            tabs.active = "mac-tab-lookup"
            await pilot.pause()

            app.query_one("#mac-lookup-input").value = "00:1A:2B:3C:4D:5E"
            app.call_from_thread = lambda func, *args: func(*args)

            mock_info = {
                "valid": True,
                "mac": "00:1A:2B:3C:4D:5E",
                "prefix": "001A2B",
                "vendor": "Test Vendor",
                "country": "US"
            }

            with patch('shared.tui_mac.MacLabManager.lookup', return_value=mock_info) as mock_lookup:
                app.query_one("#btn-mac-lookup").press()
        await pilot.pause()
                await pilot.pause(0.1) # allow thread to execute
                mock_lookup.assert_called_once_with("00:1A:2B:3C:4D:5E")

                log = app.query_one("#mac-lookup-result")
                self.assertTrue(any("Test Vendor" in line.text for line in log.lines))

if __name__ == '__main__':
    unittest.main()
