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
            tab.query_one("#btn-ascii-convert").press()
            await pilot.pause()

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
            tab.query_one("#btn-ascii-convert").press()
            await pilot.pause()

            # Manager should NOT be called
            MockManager.return_value.convert_image_to_ascii.assert_not_called()

    @patch("shared.tui_ascii.AsciiLabManager")
    async def test_play_gif(self, MockManager):
        # Setup mock for gif extraction
        mock_manager_instance = MockManager.return_value
        MockManager.CHARSETS = {"standard": "abc"}
        mock_manager_instance.CHARSETS = {"standard": "abc"}

        async with self.app.run_test() as pilot:
            tab = self.app.query_one(AsciiLabTab)

            # Override the _extract_frames method to avoid touching disk or PIL in tests
            tab._extract_frames = MagicMock(return_value=[("FRAME1", 0.1), ("FRAME2", 0.1)])

            tab.current_file = Path("animation.gif")
            tab.query_one("#btn-ascii-play").disabled = False

            # Set parameters
            tab.query_one("#ascii-width-input").value = "50"

            # Click play
            tab.query_one("#btn-ascii-play").press()
            await pilot.pause()

            # Ensure frames were extracted
            tab._extract_frames.assert_called_with(
                Path("animation.gif"),
                50,
                "standard",
                False
            )

            # Check that the timer was started
            self.assertIsNotNone(tab._animation_timer)
            self.assertEqual(len(tab._animation_frames), 2)


if __name__ == "__main__":
    unittest.main()
