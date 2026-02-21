import unittest
from unittest.mock import MagicMock, ANY
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from textual.app import App, ComposeResult
from textual.widgets import Input
from shared.tui_speed import SpeedLabTab  # noqa: E402

class SpeedLabApp(App):
    def compose(self) -> ComposeResult:
        yield SpeedLabTab(project_dir=Path("."))

class TestSpeedLabTab(unittest.IsolatedAsyncioTestCase):
    async def test_internet_speed_trigger(self):
        app = SpeedLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SpeedLabTab)
            # Mock the manager
            tab.manager = MagicMock()
            tab.manager.check_internet_speed = MagicMock()

            # Trigger button
            await pilot.click("#btn-speed-internet")

            # Wait for worker
            await pilot.pause()

            tab.manager.check_internet_speed.assert_called_once()

    async def test_disk_speed_trigger(self):
        app = SpeedLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SpeedLabTab)
            tab.manager = MagicMock()

            # Set input values
            tab.query_one("#speed-size", Input).value = "50"

            await pilot.click("#btn-speed-disk")
            await pilot.pause()

            tab.manager.check_disk_speed.assert_called_with(size_mb=50, path=ANY)

    async def test_cpu_speed_trigger(self):
        app = SpeedLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SpeedLabTab)
            tab.manager = MagicMock()

            # Reuse size input for limit
            tab.query_one("#speed-size", Input).value = "1000"

            await pilot.click("#btn-speed-cpu")
            await pilot.pause()

            tab.manager.check_cpu_speed.assert_called_with(limit=1000)

    async def test_memory_speed_trigger(self):
        app = SpeedLabApp()
        async with app.run_test() as pilot:
            tab = app.query_one(SpeedLabTab)
            tab.manager = MagicMock()

            tab.query_one("#speed-size", Input).value = "200"

            await pilot.click("#btn-speed-memory")
            await pilot.pause()

            tab.manager.check_memory_speed.assert_called_with(size_mb=200)

if __name__ == "__main__":
    unittest.main()
