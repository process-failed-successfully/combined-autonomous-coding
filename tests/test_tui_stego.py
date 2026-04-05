import unittest
from unittest.mock import MagicMock
from pathlib import Path
from textual.app import App

from shared.tui_stego import StegoLabTab


class DummyApp(App):
    def __init__(self, tab):
        super().__init__()
        self.tab = tab

    def compose(self):
        yield self.tab


class TestTuiStego(unittest.IsolatedAsyncioTestCase):
    async def test_stego_hide(self):
        tab = StegoLabTab(Path("."))
        mock_manager = MagicMock()
        tab.manager = mock_manager

        app = DummyApp(tab)
        async with app.run_test() as pilot:
            # select a file manually
            tab.selected_file = Path("dummy.png")
            tab.query_one("#stego-hide-msg").value = "hello"
            tab.query_one("#stego-hide-out").value = "out.png"

            # Click hide button
            app.query_one("#btn-stego-hide").press()
        await pilot.pause()

            mock_manager.hide.assert_called_once_with(Path("dummy.png"), Path("out.png"), "hello")

    async def test_stego_extract(self):
        tab = StegoLabTab(Path("."))
        mock_manager = MagicMock()
        mock_manager.extract.return_value = "hello world"
        tab.manager = mock_manager

        app = DummyApp(tab)
        async with app.run_test() as pilot:
            # select a file manually
            tab.selected_file = Path("dummy.png")

            # Click extract button
            app.query_one("#btn-stego-extract").press()
        await pilot.pause()

            mock_manager.extract.assert_called_once_with(Path("dummy.png"))

            # verify log
            log = tab.query_one("#stego-log")
            log_text = str(log.lines[1].text.plain if hasattr(log.lines[1].text, 'plain') else log.lines[1].text)
            self.assertIn("hello world", log_text)


if __name__ == "__main__":
    unittest.main()
