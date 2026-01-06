import unittest
from pathlib import Path
import sys

# Add the root directory to the path to import shared and ui modules
sys.path.append(str(Path(__file__).parent.parent))
from ui.tui import TUI


class TestTUI(unittest.TestCase):
    def test_tui_launches_and_displays_summary(self):
        """
        Test that the TUI launches and displays the summary.
        """
        async def run_app():
            app = TUI()
            async with app.run_test() as pilot:
                self.assertIsNotNone(pilot.app.query_one("#summary"))

        import asyncio
        asyncio.run(run_app())


if __name__ == "__main__":
    unittest.main()
