import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from textual.app import App, ComposeResult
from shared.tui_ascii import AsciiLabTab

class AsciiLabApp(App):
    def compose(self) -> ComposeResult:
        yield AsciiLabTab(project_dir=Path("."))

class TestAsciiLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = AsciiLabApp()

    @patch("shared.tui_ascii.AsciiLabManager")
    async def test_convert_image(self, MockManager):
        # Setup mock
        mock_manager_instance = MockManager.return_value
        # Ensure CHARSETS is available both on class and instance just in case
        MockManager.CHARSETS = {"standard": "abc"}
        mock_manager_instance.CHARSETS = {"standard": "abc"}
        mock_manager_instance.convert_image_to_ascii.return_value = "ASCII_ART_RESULT"

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(AsciiLabTab)

            # Verify mock injection
            # print(f"Manager in tab: {tab.manager}")

            # Simulate file selection
            tab.current_file = Path("test_image.png")
            tab.query_one("#btn-ascii-convert").disabled = False

            # Set parameters
            tab.query_one("#ascii-width-input").value = "50"

            # Click convert
            await pilot.click("#btn-ascii-convert")

            # Verify manager was called
            mock_manager_instance.convert_image_to_ascii.assert_called_with(
                Path("test_image.png"),
                width=50,
                charset="standard",
                inverse=False
            )

    @patch("shared.tui_ascii.AsciiLabManager")
    async def test_convert_no_file(self, MockManager):
        # Setup mock for this test too
        MockManager.return_value.CHARSETS = {"standard": "abc"}

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(AsciiLabTab)

            # Ensure no file selected
            tab.current_file = None

            # Click convert
            await pilot.click("#btn-ascii-convert")

            # Manager should NOT be called
            MockManager.return_value.convert_image_to_ascii.assert_not_called()

if __name__ == "__main__":
    unittest.main()
