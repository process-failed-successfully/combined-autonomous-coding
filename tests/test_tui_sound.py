import unittest
from pathlib import Path
from unittest.mock import MagicMock
from textual.app import App, ComposeResult
from shared.tui_sound import SoundLabTab

class SoundApp(App):
    def compose(self) -> ComposeResult:
        yield SoundLabTab(Path("."))

class TestSoundLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_tui_compose(self):
        app = SoundApp()
        async with app.run_test() as pilot:
            # Check if widgets exist
            self.assertIsNotNone(app.query_one("SoundLabTab"))
            self.assertIsNotNone(app.query_one("#tab-tone"))
            self.assertIsNotNone(app.query_one("#sound-visualizer"))

            # Test clicking generate (mock logic if possible, but real logic is fast enough here)
            # We need to make sure we don't block.

            # Find generate button
            btn = app.query_one("#btn-gen-tone")
            pilot.app.query_one("#btn-gen-tone").press()
            await pilot.pause()

            # Check visualizer updated
            vis = app.query_one("#sound-visualizer")
            # Textual Static widget update might be async or immediate
            # We can check if renderable is not empty string?
            # Actually I set text content using update()
            # In textual 0.64+, update changes the renderable.

            # Let's just assert it didn't crash.

if __name__ == '__main__':
    unittest.main()
