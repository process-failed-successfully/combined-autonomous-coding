import unittest
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))

class TestEntropyLabTUI(unittest.IsolatedAsyncioTestCase):
    async def test_tui_render_and_interact(self):
        try:
            from textual.app import App, ComposeResult
            from shared.tui_entropy import EntropyLabTab

            class DummyApp(App):
                def compose(self) -> ComposeResult:
                    yield EntropyLabTab()

            app = DummyApp()
            async with app.run_test(headless=True) as pilot:
                tab = app.query_one(EntropyLabTab)
                self.assertIsNotNone(tab)

                input_area = app.query_one("#entropy-input-text")
                output_area = app.query_one("#entropy-output-text")

                # Test Analyze
                input_area.text = "ABAB"
                await pilot.click("#btn-entropy-analyze")

                # Should be 4 bytes and 1.0 entropy
                self.assertIn("Size: 4 bytes", output_area.text)
                self.assertIn("Entropy: 1.0000", output_area.text)

                # Test Clear
                await pilot.click("#btn-entropy-clear")
                self.assertEqual(input_area.text, "")
                self.assertEqual(output_area.text, "")

        except ImportError:
            self.skipTest("Textual not installed")
