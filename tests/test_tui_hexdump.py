import unittest
from unittest.mock import patch, MagicMock

try:
    import textual
    from textual.app import App
    from textual.widgets import Input, Button, RichLog, RadioSet
    from shared.tui_hexdump import HexdumpLabTab
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = object

@unittest.skipIf(not TEXTUAL_AVAILABLE, "Textual not available")
class TestHexdumpLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        class DummyApp(App):
            def compose(self):
                yield HexdumpLabTab()

        self.app = DummyApp()
        self._app_cm = self.app.run_test(headless=True, size=(100, 40))
        self.pilot = await self._app_cm.__aenter__()

    async def asyncTearDown(self):
        await self._app_cm.__aexit__(None, None, None)

    async def test_initial_render(self):
        """Test the initial rendering of the tab."""
        tab = self.app.query_one(HexdumpLabTab)
        self.assertIsNotNone(tab)

        input_widget = tab.query_one("#hexdump-input", Input)
        self.assertEqual(input_widget.placeholder, "Enter text or file path...")

        offset_widget = tab.query_one("#hexdump-offset", Input)
        self.assertEqual(offset_widget.value, "0")

        length_widget = tab.query_one("#hexdump-length", Input)
        self.assertEqual(length_widget.value, "-1")

    @patch("shared.tui_hexdump.HexdumpManager.hexdump")
    async def test_generate_text_hexdump(self, mock_hexdump):
        """Test generating hexdump from text input."""
        mock_hexdump.return_value = "mock_hexdump_output"

        tab = self.app.query_one(HexdumpLabTab)
        input_widget = tab.query_one("#hexdump-input", Input)
        input_widget.value = "test string"

        # Default is text type radio button

        generate_btn = tab.query_one("#hexdump-generate-btn", Button)
        await self.pilot.click("#hexdump-generate-btn")

        mock_hexdump.assert_called_once_with(b"test string", offset=0)

        output_log = tab.query_one("#hexdump-output", RichLog)
        lines = [line.text for line in output_log.lines]

        self.assertTrue(any("--- Hex Dump ---" in line for line in lines))
        self.assertTrue(any("mock_hexdump_output" in line for line in lines))

    async def test_clear_output(self):
        """Test clearing the output log."""
        tab = self.app.query_one(HexdumpLabTab)
        output_log = tab.query_one("#hexdump-output", RichLog)

        output_log.write("some test data")

        clear_btn = tab.query_one("#hexdump-clear-btn", Button)
        await self.pilot.click("#hexdump-clear-btn")

        self.assertEqual(len(output_log.lines), 0)

if __name__ == "__main__":
    unittest.main()
